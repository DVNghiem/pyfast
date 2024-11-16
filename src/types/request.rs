use axum::extract::Multipart;
use axum::extract::{FromRequest, Request as HttpRequest};
use axum::response::IntoResponse;
use axum::Json;
use http::header;
use pyo3::types::{PyDict, PyString};
use pyo3::{exceptions::PyValueError, prelude::*};
use serde_json::Value;
use std::collections::HashMap;
use std::io::Write;
use tempfile::NamedTempFile;

use super::{header::Headers, multimap::QueryParams};

#[derive(Debug, Clone)]
#[pyclass]
struct UploadedFile {

    #[pyo3(get)]
    name: String,

    #[pyo3(get)]
    content_type: String,

    #[pyo3(get)]
    path: std::path::PathBuf,
}

#[derive(Debug, Default, Clone)]
#[pyclass]
pub struct BodyData {

    #[pyo3(get)]
    json: Vec<u8>,

    #[pyo3(get)]
    files: Vec<UploadedFile>,
}

#[derive(Default, Debug, Clone, FromPyObject)]
pub struct Request {
    pub query_params: QueryParams,
    pub headers: Headers,
    pub method: String,
    pub path_params: HashMap<String, String>,
    pub body: BodyData,
}

impl ToPyObject for Request {
    fn to_object(&self, py: Python) -> PyObject {
        let query_params = self.query_params.clone();
        let headers: Py<Headers> = self.headers.clone().into_py(py).extract(py).unwrap();
        let path_params = self.path_params.clone().into_py(py).extract(py).unwrap();
        let body = self.body.clone().into_py(py).extract(py).unwrap();

        let request = PyRequest {
            query_params,
            path_params,
            headers,
            body,
            method: self.method.clone(),
        };
        Py::new(py, request).unwrap().as_ref(py).into()
    }
}

impl Request {
    pub async fn from_request(request: HttpRequest) -> Self {
        let mut query_params: QueryParams = QueryParams::new();

        // setup query params
        if let Some(qs) = request.uri().query() {
            for (key, value) in qs.split('&').filter_map(|s| {
                let mut split = s.splitn(2, '=');
                Some((split.next()?, split.next()?))
            }) {
                query_params.set(key.to_string(), value.to_string());
            }
        }

        // parse the header to python header object
        let headers = Headers::from_hyper_headers(request.headers());
        let method = request.method().to_string();
        let content_type = request
            .headers()
            .get(header::CONTENT_TYPE)
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");
        let default_body = BodyData::default();
        let body = match content_type {
            t if t.starts_with("application/json") => {
                let json = Json::<Vec<u8>>::from_request(request, &())
                    .await
                    .map_err(|e| e.into_response());
                match json {
                    Ok(json) => BodyData {
                        json: json.to_vec(),
                        files: vec![],
                    },
                    Err(_e) => default_body,
                }
            }
            t if t.starts_with("multipart/form-data") => {
                let mut multipart = Multipart::from_request(request, &())
                    .await
                    .map_err(|e| e.into_response());

                let mut files = vec![];
                let mut json = vec![];

                while let Some(field) = multipart
                    .as_mut()
                    .unwrap()
                    .next_field()
                    .await
                    .map_err(|e| e.into_response())
                    .ok()
                    .flatten()
                {
                    let name = field.name().unwrap_or("").to_string();
                    let content_type = field
                        .content_type()
                        .unwrap_or("application/octet-stream")
                        .to_string();

                    if name == "json" {
                        let data = field.bytes().await.map_err(|e| e.into_response());
                        json = match Some(serde_json::from_slice(&data.unwrap()).map_err(|e| e)) {
                            Some(Ok(json)) => json,
                            _ => vec![],
                        }
                    } else {
                        let data = field.bytes().await.map_err(|e| e.into_response());

                        let mut temp_file = NamedTempFile::new().map_err(|e| e);

                        match temp_file {
                            Ok(ref mut file) => {
                                let _ = file.write(&data.unwrap()).map_err(|e| e);
                                files.push(UploadedFile {
                                    name,
                                    content_type,
                                    path: file.path().to_path_buf(),
                                });
                            }
                            Err(e) => {
                                eprintln!("Error: {:?}", e);
                            }
                        }
                    }
                }

                BodyData { json, files }
            }
            _ => default_body,
        };

        Self {
            query_params,
            headers: headers.clone(),
            method,
            path_params: HashMap::new(),
            body: body,
        }
    }
}

#[pyclass(name = "Request")]
#[derive(Clone)]
pub struct PyRequest {
    #[pyo3(get, set)]
    pub query_params: QueryParams,
    #[pyo3(get, set)]
    pub headers: Py<Headers>,
    #[pyo3(get, set)]
    pub path_params: Py<PyDict>,
    #[pyo3(get)]
    pub body: Py<BodyData>,
    #[pyo3(get)]
    pub method: String,
}

#[pymethods]
impl PyRequest {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        query_params: QueryParams,
        headers: Py<Headers>,
        path_params: Py<PyDict>,
        body: Py<BodyData>,
        method: String,
    ) -> Self {
        Self {
            query_params,
            headers,
            path_params,
            body,
            method,
        }
    }

    #[setter]
    pub fn set_body(&mut self, body: Py<BodyData>) -> PyResult<()> {
        self.body = body;
        Ok(())
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        match self.body.as_ref(py).downcast::<PyString>() {
            Ok(python_string) => match serde_json::from_str(python_string.extract()?) {
                Ok(Value::Object(map)) => {
                    let dict = PyDict::new(py);

                    for (key, value) in map.iter() {
                        let py_key = key.to_string().into_py(py);
                        let py_value = match value {
                            Value::String(s) => s.as_str().into_py(py),
                            _ => value.to_string().into_py(py),
                        };

                        dict.set_item(py_key, py_value)?;
                    }

                    Ok(dict.into_py(py))
                }
                _ => Err(PyValueError::new_err("Invalid JSON object")),
            },
            Err(e) => Err(e.into()),
        }
    }
}
