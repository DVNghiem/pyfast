mod utils;
mod cache;
mod openapi;
use pyo3::prelude::*;


#[pymodule]
fn pyfast(py: Python<'_>, m: &PyModule) -> PyResult<()>  {

    let cache_module = PyModule::new(py, "cache")?;
    cache_module.add_class::<cache::backend::BaseBackend>()?;
    cache_module.add_class::<cache::redis_backend::RedisBackend>()?;

    m.add_submodule(&cache_module)?;
    m.add_class::<openapi::schemas::BaseSchemaGenerator>()?;
    m.add_class::<openapi::swagger::SwaggerUI>()?;    

    pyo3::prepare_freethreaded_python();
    Ok(())
}
