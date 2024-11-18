use pyo3::{
    prelude::*,
    types::{PyBytes, PyDict},
};

use super::header::Header;
use crate::utils::get_description_from_pyobject;


#[derive(Debug, Clone, FromPyObject)]
pub struct Response {
    pub status_code: u16,
    pub response_type: String,
    pub headers: Header,

    #[pyo3(from_py_with = "get_description_from_pyobject")]
    pub description: Vec<u8>,
    pub file_path: Option<String>,
}

impl Response {
    pub fn not_found(headers: Option<&Header>) -> Self {
        let headers = match headers {
            Some(headers) => headers.clone(),
            None => Header::new(None),
        };

        Self {
            status_code: 404,
            response_type: "text".to_string(),
            headers,
            description: "Not found".to_owned().into_bytes(),
            file_path: None,
        }
    }

    pub fn internal_server_error(headers: Option<&Header>) -> Self {
        let headers = match headers {
            Some(headers) => headers.clone(),
            None => Header::new(None),
        };

        Self {
            status_code: 500,
            response_type: "text".to_string(),
            headers,
            description: "Internal server error".to_owned().into_bytes(),
            file_path: None,
        }
    }
}

impl ToPyObject for Response {
    fn to_object(&self, py: Python) -> PyObject {
        let headers = self.headers.clone().into_py(py).extract(py).unwrap();
        // The description should only be either string or binary.
        // it should raise an exception otherwise
        let description = match String::from_utf8(self.description.to_vec()) {
            Ok(description) => description.to_object(py),
            Err(_) => PyBytes::new(py, &self.description.to_vec()).into(),
        };

        let response = PyResponse {
            status_code: self.status_code,
            response_type: self.response_type.clone(),
            headers,
            description,
            file_path: self.file_path.clone(),
        };
        Py::new(py, response).unwrap().as_ref(py).into()
    }
}

#[pyclass(name = "Response")]
#[derive(Debug, Clone)]
pub struct PyResponse {
    #[pyo3(get)]
    pub status_code: u16,
    #[pyo3(get)]
    pub response_type: String,
    #[pyo3(get, set)]
    pub headers: Py<Header>,
    #[pyo3(get)]
    pub description: Py<PyAny>,
    #[pyo3(get)]
    pub file_path: Option<String>,
}

#[pymethods]
impl PyResponse {
    // To do: Add check for content-type in header and change response_type accordingly
    #[new]
    pub fn new(
        py: Python,
        status_code: u16,
        headers: &PyAny,
        description: Py<PyAny>,
    ) -> PyResult<Self> {
        let headers_output: Py<Header> = if let Ok(headers_dict) = headers.downcast::<PyDict>() {
            // Here you'd have logic to create a Headers instance from a PyDict
            // For simplicity, let's assume you have a method `from_dict` on Headers for this
            let headers = Header::new(Some(headers_dict)); // Hypothetical method
            Py::new(py, headers)?
        } else if let Ok(headers) = headers.extract::<Py<Header>>() {
            // If it's already a Py<Headers>, use it directly
            headers
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "headers must be a Headers instance or a dict",
            ));
        };

        Ok(Self {
            status_code,
            // we should be handling based on headers but works for now
            response_type: "text".to_string(),
            headers: headers_output,
            description,
            file_path: None,
        })
    }

    #[setter]
    pub fn set_description(&mut self, description: Py<PyAny>) -> PyResult<()> {
        self.description = description;
        Ok(())
    }

    pub fn set_cookie(&mut self, py: Python, key: &str, value: &str) -> PyResult<()> {
        self.headers
            .try_borrow_mut(py)
            .expect("value already borrowed")
            .append(key.to_string(), value.to_string());
        Ok(())
    }
}