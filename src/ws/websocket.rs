use std::sync::{Arc, Mutex as StdMutex};

use axum::{
    extract::{
        ws::{Message, WebSocket},
        WebSocketUpgrade,
    },
    response::Response,
};
use pyo3::{
    prelude::*,
    types::PyDict,
};
use tokio::sync::{mpsc, Mutex};

#[derive(Debug, Clone)]
pub enum WebSocketMessage {
    Text(String),
    Binary(Vec<u8>),
    Close,
}

#[pyclass]
pub struct WebSocketSession {
    tx_send: StdMutex<mpsc::Sender<WebSocketMessage>>,
    is_closed: StdMutex<bool>,
}

impl WebSocketSession {
    pub fn from_sender(sender: mpsc::Sender<WebSocketMessage>) -> Self {
        WebSocketSession {
            tx_send: StdMutex::new(sender),
            is_closed: StdMutex::new(false),
        }
    }
}

#[pymethods]
impl WebSocketSession {
    #[new]
    fn new() -> Self {
        let (tx_send, _) = mpsc::channel(100);

        WebSocketSession {
            tx_send: StdMutex::new(tx_send),
            is_closed: StdMutex::new(false),
        }
    }

    fn send(&self, message: &PyAny) -> PyResult<()> {
        // check socket is closed
        if *self.is_closed.lock().unwrap() {
            return Err(PyErr::new::<pyo3::exceptions::PyConnectionError, _>(
                "WebSocket closed",
            ));
        }

        // send message
        let msg = if let Ok(text) = message.extract::<String>() {
            WebSocketMessage::Text(text)
        } else if let Ok(bytes) = message.extract::<Vec<u8>>() {
            WebSocketMessage::Binary(bytes)
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "Unsupported message type",
            ));
        };

        let tx = self.tx_send.lock().unwrap().clone();

        tokio::task::spawn_blocking(move || {
            let _ = tokio::runtime::Runtime::new().unwrap().block_on(async {
                tx.send(msg).await.map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyConnectionError, _>("Failed to send message")
                })
            });
        });
        Ok(())
    }

    // close connection
    fn close(&self) -> PyResult<()> {
        let mut is_closed = self.is_closed.lock().unwrap();
        *is_closed = true;

        let tx = self.tx_send.lock().unwrap().clone();

        tokio::runtime::Runtime::new().unwrap().block_on(async {
            println!("Closing connection *close");
            tx.send(WebSocketMessage::Close).await.map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyConnectionError, _>("Failed to close")
            })
        })
    }
}

pub async fn websocket_handler(handler: PyObject, ws: WebSocketUpgrade) -> Response {
    ws.on_upgrade(move |socket| handle_socket(handler, socket))
}

async fn handle_socket(python_handler: PyObject, socket: WebSocket) {
    let (tx_send, mut rx_send) = mpsc::channel(100);
    let (tx_recv, _) = mpsc::channel(100);

    let is_closed = Arc::new(Mutex::new(false));
    let is_closed_clone = is_closed.clone();

    let socket = Arc::new(Mutex::new(socket));

    let socket_send = socket.clone();

    // flow send message to socket
    tokio::spawn(async move {
        while let Some(msg) = rx_send.recv().await {
            let mut socket = socket_send.lock().await;
            let send_result = match msg {
                WebSocketMessage::Text(text) => {
                    socket.send(Message::Text(text)).await
                },
                WebSocketMessage::Binary(bytes) => socket.send(Message::Binary(bytes)).await,
                WebSocketMessage::Close => {
                    println!("Closing connection");
                    break;
                }
            };

            if send_result.is_err() {
                break;
            }
        }
    });

    // receive message from socket

    let socket_recv = socket.clone();
    tokio::spawn(async move {
        let mut socket = socket_recv.lock().await;

        while let Some(msg) = socket.recv().await {

            match msg {
                Ok(Message::Text(text)) => {
                    Python::with_gil(|py| {
                        let session = WebSocketSession::from_sender(tx_send.clone());
                        let kwargs = PyDict::new(py);
                        kwargs.set_item("message", text.clone()).unwrap();
                        let _ = python_handler.call(py, (session, ), Some(kwargs));
                    });

                    if tx_recv.send(WebSocketMessage::Text(text)).await.is_err() {
                        break;
                    }
                }
                Ok(Message::Binary(bytes)) => {
                    if tx_recv.send(WebSocketMessage::Binary(bytes)).await.is_err() {
                        break;
                    }
                }
                Ok(Message::Ping(ping)) => {
                    if socket.send(Message::Pong(ping)).await.is_err() {
                        break;
                    }
                }
                Ok(Message::Pong(_)) => {
                    // Handle pong message if necessary
                }
                Ok(Message::Close(_)) | Err(_) => {
                    let mut closed = is_closed_clone.lock().await;
                    *closed = true;
                    break;
                }
            }
        }
    });
}
