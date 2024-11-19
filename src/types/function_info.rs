use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};

use pyo3::prelude::*;

#[pyclass]
#[derive(Debug, PartialEq, Eq, Hash)]
pub enum MiddlewareType {
    #[pyo3(name = "BEFORE_REQUEST")]
    BeforeRequest = 0,
    #[pyo3(name = "AFTER_REQUEST")]
    AfterRequest = 1,
}

#[pymethods]
impl MiddlewareType {
    // This is needed because pyo3 doesn't support hashing enums from Python
    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    #[pyo3(get, set)]
    pub handler: Py<PyAny>,
    #[pyo3(get, set)]
    pub is_async: bool,
}

#[pymethods]
impl FunctionInfo {
    #[new]
    pub fn new(
        handler: Py<PyAny>,
        is_async: bool,
    ) -> Self {
        Self {
            handler,
            is_async,
        }
    }

    fn __str__(&self) -> PyResult<String> {
        Ok(format!("Function(handler = {:?}, is_async = {})", self.handler, self.is_async))
    }
}
