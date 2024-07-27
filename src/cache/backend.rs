use pyo3::prelude::*;

#[pyclass(subclass)]
pub struct BaseBackend {}

#[pymethods]
impl BaseBackend {
    #[new]
    fn new() -> Self {
        BaseBackend {}
    }

    fn get(&self, _key: &str) {
        unimplemented!()
    }

    fn set(&self, _response: &str, _key: &str, _ttl: &str) {
        unimplemented!()
    }

    fn delete_startswith(&self, _value: &str) {
        unimplemented!()
    }
}
