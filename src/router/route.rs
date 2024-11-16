use pyo3::prelude::*;

use crate::types::function_info::FunctionInfo;


#[pyclass]
#[derive(Debug, Clone)]
pub struct Route {
    #[pyo3(get, set)]
    pub path: String,

    #[pyo3(get, set)]
    pub function: FunctionInfo,

    #[pyo3(get, set)]
    pub method: String,
}

#[pymethods]
impl Route {

    #[new]
    pub fn new(path: &str, function: FunctionInfo, method: String) -> Self {
        Self {
            path: path.to_string(),
            function,
            method
        }
    }
}

