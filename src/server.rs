use crate::{
    executor::execute_http_function,
    router::{router::Router, ws::WebSocketRouter},
    socket::SocketHeld,
    types::{function_info::FunctionInfo, request::Request},
};
use http::{HeaderMap, StatusCode};
use pyo3::{exceptions::PyValueError, prelude::*};
use std::{
    env,
    sync::{
        atomic::Ordering::{Relaxed, SeqCst},
        Mutex,
    },
    thread, time::Duration,
};
use std::{
    process::exit,
    sync::{atomic::AtomicBool, Arc},
};

use axum::{
    body::Body,
    extract::Request as HttpRequest,
    response::{IntoResponse, Response},
    routing::{delete, get, post, put},
    Router as RouterServer,
};

static STARTED: AtomicBool = AtomicBool::new(false);
const MAX_PAYLOAD_SIZE: &str = "MAX_PAYLOAD_SIZE";
const DEFAULT_MAX_PAYLOAD_SIZE: usize = 1_000_000; // 1Mb


#[pyclass]
pub struct Server {
    router: Arc<Mutex<Router>>,
    websocket_router: Arc<WebSocketRouter>,
    startup_handler: Option<Arc<FunctionInfo>>,
    shutdown_handler: Option<Arc<FunctionInfo>>,
    excluded_response_headers_paths: Option<Vec<String>>,
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        Self {
            router: Arc::new(Mutex::new(Router::default())),
            websocket_router: Arc::new(WebSocketRouter::new()),
            startup_handler: None,
            shutdown_handler: None,
            excluded_response_headers_paths: None,
        }
    }

    pub fn set_router(&mut self, router: Router) {
        self.router = Arc::new(Mutex::new(router));
    }

    pub fn start(
        &mut self,
        py: Python,
        socket: &PyCell<SocketHeld>,
        workers: usize,
        processes: usize,
    ) -> PyResult<()> {
        pyo3_log::init();

        if STARTED
            .compare_exchange(false, true, SeqCst, Relaxed)
            .is_err()
        {
            // debug!("Robyn is already running...");
            return Ok(());
        }

        let raw_socket = socket.try_borrow_mut()?.get_socket();

        let router = self.router.clone();
        let _web_socket_router = self.websocket_router.clone();

        let asyncio = py.import("asyncio")?;
        let event_loop = asyncio.call_method0("new_event_loop")?;
        asyncio.call_method1("set_event_loop", (event_loop,))?;

        let _startup_handler = self.startup_handler.clone();
        let shutdown_handler = self.shutdown_handler.clone();

        let excluded_response_headers_paths = self.excluded_response_headers_paths.clone();

        let task_locals = pyo3_asyncio::TaskLocals::new(event_loop).copy_context(py)?;
        let task_locals_copy = task_locals.clone();

        let _max_payload_size = env::var(MAX_PAYLOAD_SIZE)
            .unwrap_or(DEFAULT_MAX_PAYLOAD_SIZE.to_string())
            .trim()
            .parse::<usize>()
            .map_err(|e| {
                PyValueError::new_err(format!(
                    "Failed to parse environment variable {MAX_PAYLOAD_SIZE} - {e}"
                ))
            })?;

        thread::spawn(move || {
            let rt = tokio::runtime::Builder::new_multi_thread()
                .worker_threads(workers)
                .max_blocking_threads(processes)
                .thread_keep_alive(Duration::from_secs(60))
                .thread_name("hypern-worker")
                .enable_all()
                .build()
                .unwrap();
            rt.block_on(async move {
                let task_locals = task_locals_copy.clone();
                // tracing_subscriber::fmt()
                // .with_max_level(tracing::Level::DEBUG)
                // .init();
                let mut app = RouterServer::new();

                // handle logic for each route with pyo3
                for route in router.lock().unwrap().iter() {
                    let task_locals = task_locals.clone();
                    let route_copy = route.clone();
                    let function = route_copy.function.clone();
                    let path = route_copy.path.clone();
                    let excluded_headers = excluded_response_headers_paths.clone();

                    app = match route.method.as_str() {
                        "GET" => app.route(
                            &path,
                            get(move |req| {
                                mapping_method(req, function, excluded_headers, task_locals.clone())
                            }),
                        ),
                        "POST" => app.route(
                            &path,
                            post(move |req| {
                                mapping_method(req, function, excluded_headers, task_locals.clone())
                            }),
                        ),
                        "PUT" => app.route(
                            &path,
                            put(move |req| {
                                mapping_method(req, function, excluded_headers, task_locals.clone())
                            }),
                        ),
                        "DELETE" => app.route(
                            &path,
                            delete(move |req| {
                                mapping_method(req, function, excluded_headers, task_locals.clone())
                            }),
                        ),
                        _ => app,
                    };
                }
                // run our app with hyper, listening globally on port 3000
                let listener = tokio::net::TcpListener::from_std(raw_socket.into()).unwrap();
                axum::serve(listener, app).await.unwrap();

            });
        });

        let event_loop = (*event_loop).call_method0("run_forever");
        if event_loop.is_err() {
            // debug!("Ctrl c handler");

            if let Some(function) = shutdown_handler {
                if function.is_async {
                    pyo3_asyncio::tokio::run_until_complete(
                        task_locals.event_loop(py),
                        pyo3_asyncio::into_future_with_locals(
                            &task_locals.clone(),
                            function.handler.as_ref(py).call0()?,
                        )
                        .unwrap(),
                    )
                    .unwrap();
                } else {
                    Python::with_gil(|py| function.handler.call0(py))?;
                }
            }

            exit(0);
        }
        Ok(())
    }
}

async fn execute_request(
    req: HttpRequest<Body>,
    function: FunctionInfo,
    excluded_headers: Option<Vec<String>>,
) -> Response {
    let request = Request::from_request(req).await;
    match execute_http_function(&request, &function).await {
        Ok(response) => {
            let mut headers = HeaderMap::new();
            for (key, value) in response.headers.headers {
                if !excluded_headers
                    .as_ref()
                    .map(|excluded| excluded.contains(&key))
                    .unwrap_or(false)
                {
                    let header_name = http::header::HeaderName::from_bytes(key.as_bytes()).unwrap();
                    headers.insert(header_name, value.join(" ").parse().unwrap());
                }
            }

            let mut response_builder =
                Response::builder().status(StatusCode::from_u16(response.status_code).unwrap());
            for (key, value) in headers {
                if let Some(k) = key {
                    response_builder = response_builder.header(k, value);
                }
            }
            response_builder
                .body(Body::from(response.description))
                .unwrap()
        }
        Err(e) => Response::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body(Body::from(format!("Error: {}", e)))
            .unwrap(),
    }
}

async fn mapping_method(
    req: HttpRequest<Body>,
    function: FunctionInfo,
    excluded_headers: Option<Vec<String>>,
    task_locals: pyo3_asyncio::TaskLocals,
) -> impl IntoResponse {
    pyo3_asyncio::tokio::scope(
        task_locals,
        execute_request(req, function, excluded_headers),
    )
    .await
}
