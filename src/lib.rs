mod utils;
mod cache;
mod openapi;
use pyo3::prelude::*;


#[pymodule]
fn pyfast(_py: Python<'_>, m: &PyModule) -> PyResult<()>  {

    m.add_class::<cache::backend::BaseBackend>()?;
    m.add_class::<cache::redis_backend::RedisBackend>()?;

    m.add_class::<openapi::schemas::BaseSchemaGenerator>()?;
    m.add_class::<openapi::swagger::SwaggerUI>()?;    

    pyo3::prepare_freethreaded_python();
    Ok(())
}
