use crate::{
    executor::{execute_http_function, execute_middleware_function},
    middlewares::base::Middleware,
    router::router::Router,
    types::{function_info::FunctionInfo, middleware::MiddlewareReturn, request::Request},
    ws::{
        router::WebsocketRouter, socket::SocketHeld,
        websocket::websocket_handler,
    },
};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyDict};
use std::{
    collections::HashMap,
    env,
    sync::{
        atomic::Ordering::{Relaxed, SeqCst},
        Mutex,
    },
    thread,
    time::Duration,
};
use std::{
    process::exit,
    sync::{atomic::AtomicBool, Arc},
};

use axum::{
    body::Body,
    extract::{Request as HttpRequest, WebSocketUpgrade},
    http::StatusCode,
    response::{IntoResponse, Response as ServerResponse},
    routing::{any, delete, get, head, options, patch, post, put, trace},
    Extension, Router as RouterServer,
};

use tower_http::{
    trace::{DefaultOnResponse, TraceLayer},
    LatencyUnit,
};
use tracing::{debug, Level};
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt};

use crate::di::DependencyInjection;

static STARTED: AtomicBool = AtomicBool::new(false);
const MAX_PAYLOAD_SIZE: &str = "MAX_PAYLOAD_SIZE";
const DEFAULT_MAX_PAYLOAD_SIZE: usize = 1_000_000; // 1Mb

#[pyclass]
pub struct Server {
    router: Arc<Mutex<Router>>,
    websocket_router: Arc<WebsocketRouter>,
    startup_handler: Option<Arc<FunctionInfo>>,
    shutdown_handler: Option<Arc<FunctionInfo>>,
    injected: DependencyInjection,
    middlewares: Middleware,
    extra_headers: Arc<Mutex<HashMap<String, String>>>,
}

#[pymethods]
impl Server {
    #[new]
    pub fn new() -> Self {
        let inject = DependencyInjection::new();
        let middlewares = Middleware::new().unwrap();
        Self {
            router: Arc::new(Mutex::new(Router::default())),
            websocket_router: Arc::new(WebsocketRouter::default()),
            startup_handler: None,
            shutdown_handler: None,
            injected: inject,
            middlewares,
            extra_headers: Arc::new(HashMap::new().into()),
        }
    }

    pub fn set_router(&mut self, router: Router) {
        self.router = Arc::new(Mutex::new(router));
    }

    pub fn set_websocket_router(&mut self, websocket_router: WebsocketRouter) {
        self.websocket_router = Arc::new(websocket_router);
    }

    pub fn inject(&mut self, key: &str, value: Py<PyAny>) {
        let _ = self.injected.add_dependency(key, value);
    }

    pub fn set_injected(&mut self, injected: Py<PyDict>) {
        self.injected = DependencyInjection::from_object(injected);
    }

    pub fn set_before_hooks(&mut self, hooks: Vec<FunctionInfo>) {
        self.middlewares.set_before_hooks(hooks);
    }

    pub fn set_after_hooks(&mut self, hooks: Vec<FunctionInfo>) {
        self.middlewares.set_after_hooks(hooks);
    }

    pub fn set_response_headers(&mut self, headers: HashMap<String, String>) {
        let mut extra_headers = self.extra_headers.lock().unwrap();
        *extra_headers = headers;
    }

    pub fn start(
        &mut self,
        py: Python,
        socket: &PyCell<SocketHeld>,
        workers: usize,
        max_blocking_threads: usize,
    ) -> PyResult<()> {
        tracing_subscriber::registry()
            .with(
                tracing_subscriber::EnvFilter::try_from_default_env()
                    .unwrap_or_else(|_| "debug".into()),
            )
            .with(fmt::layer().with_target(false).with_level(true))
            .init();

        if STARTED
            .compare_exchange(false, true, SeqCst, Relaxed)
            .is_err()
        {
            return Ok(());
        }

        let raw_socket = socket.try_borrow_mut()?.get_socket();

        let router = self.router.clone();
        let websocket_router = self.websocket_router.clone();

        let asyncio = py.import("asyncio")?;
        let event_loop = asyncio.call_method0("new_event_loop")?;
        asyncio.call_method1("set_event_loop", (event_loop,))?;

        let _startup_handler = self.startup_handler.clone();
        let shutdown_handler = self.shutdown_handler.clone();

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

        let inject_copy = self.injected.clone();
        let copy_middlewares = self.middlewares.clone();
        let extra_headers = self.extra_headers.clone().lock().unwrap().clone();
        thread::spawn(move || {
            let rt = tokio::runtime::Builder::new_multi_thread()
                .worker_threads(workers)
                .max_blocking_threads(max_blocking_threads)
                .thread_keep_alive(Duration::from_secs(60))
                .thread_name("hypern-worker")
                .enable_all()
                .build()
                .unwrap();
            debug!(
                "Server start with {} workers and {} max blockingthreads",
                workers, max_blocking_threads
            );
            debug!("Waiting for process to start...");

            rt.block_on(async move {
                let task_locals = task_locals_copy.clone();
                let mut app = RouterServer::new();

                // handle logic for each route with pyo3
                for route in router.lock().unwrap().iter() {
                    let task_locals = task_locals.clone();
                    let route_copy = route.clone();
                    let function = route_copy.function.clone();

                    let copy_middlewares_clone = copy_middlewares.clone();
                    let extra_headers = extra_headers.clone();
                    let handler = move |req| {
                        mapping_method(
                            req,
                            function,
                            task_locals,
                            copy_middlewares_clone.clone(),
                            extra_headers.clone(),
                        )
                    };

                    app = match route.method.as_str() {
                        "GET" => app.route(&route.path, get(handler)),
                        "POST" => app.route(&route.path, post(handler)),
                        "PUT" => app.route(&route.path, put(handler)),
                        "DELETE" => app.route(&route.path, delete(handler)),
                        "PATCH" => app.route(&route.path, patch(handler)),
                        "HEAD" => app.route(&route.path, head(handler)),
                        "OPTIONS" => app.route(&route.path, options(handler)),
                        "TRACE" => app.route(&route.path, trace(handler)),
                        // Handle any custom methods using the any() method
                        _ => app.route(&route.path, any(handler)),
                    };
                }

                // handle logic for each websocket route with pyo3
                for ws_route in websocket_router.iter() {
                    let ws_route_copy = ws_route.clone();
                    let handler = move |ws: WebSocketUpgrade| {
                        websocket_handler(ws_route_copy.handler.clone(), ws)
                    };
                    app = app.route(&ws_route.path, any(handler));
                }

                app = app.layer(Extension(inject_copy.clone()));
                app = app.layer(
                    TraceLayer::new_for_http().on_response(
                        DefaultOnResponse::new()
                            .level(Level::INFO)
                            .latency_unit(LatencyUnit::Millis),
                    ),
                );
                debug!("Application started");
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

#[allow(clippy::too_many_arguments)]
async fn execute_request(
    req: HttpRequest<Body>,
    function: FunctionInfo,
    middlewares: Middleware,
    extra_headers: HashMap<String, String>,
) -> ServerResponse {
    let deps = req.extensions().get::<DependencyInjection>().cloned();
    let mut request = Request::from_request(req).await;

    let mut response_builder = ServerResponse::builder();
    let headers = extra_headers
        .iter()
        .map(|(key, value)| (key.as_str(), value.as_str()))
        .collect::<Vec<_>>();
    for (key, value) in headers {
        response_builder = response_builder.header(key, value);
    }

    for before_middleware in middlewares.get_before_hooks() {
        request = match execute_middleware_function(&request, &before_middleware).await {
            Ok(MiddlewareReturn::Request(r)) => r,
            Ok(MiddlewareReturn::Response(r)) => {
                return r.to_axum_response(extra_headers);
            }
            Err(e) => {
                response_builder = response_builder.status(StatusCode::INTERNAL_SERVER_ERROR);
                return response_builder
                    .body(Body::from(format!("Error: {}", e)))
                    .unwrap();
            }
        };
    }

    let mut response = execute_http_function(&request, &function, deps)
        .await
        .unwrap();

    for after_middleware in middlewares.get_after_hooks() {
        response = match execute_middleware_function(&response, &after_middleware).await {
            Ok(MiddlewareReturn::Request(_)) => {
                return response_builder
                    .status(StatusCode::INTERNAL_SERVER_ERROR)
                    .body(Body::from("Middleware returned a response"))
                    .unwrap();
            }
            Ok(MiddlewareReturn::Response(r)) => {
                let response = r;
                response
            }
            Err(e) => {
                return response_builder
                    .status(StatusCode::INTERNAL_SERVER_ERROR)
                    .body(Body::from(e.to_string()))
                    .unwrap();
            }
        };
    }

    response.to_axum_response(extra_headers)
}

async fn mapping_method(
    req: HttpRequest<Body>,
    function: FunctionInfo,
    task_locals: pyo3_asyncio::TaskLocals,
    middlewares: Middleware,
    extra_headers: HashMap<String, String>,
) -> impl IntoResponse {
    pyo3_asyncio::tokio::scope(
        task_locals,
        execute_request(req, function, middlewares, extra_headers),
    )
    .await
}
