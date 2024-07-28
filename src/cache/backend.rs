use pyo3::prelude::*;

#[pyclass(subclass)]
pub struct BaseBackend {}

#[pymethods]
impl BaseBackend {
    #[new]
    pub fn new() -> Self {
        BaseBackend {}
    }

    pub fn get(&self, _key: String) -> PyResult<Option<String>> {
        unimplemented!()
    }

    pub fn set(&self, _response: String, _key: String, _ttl: String) {
        unimplemented!()
    }

    pub fn delete_startswith(&self, _value: String) {
        unimplemented!()
    }
}
