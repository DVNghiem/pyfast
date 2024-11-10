mod utils;
mod cache;
mod openapi;
mod background;
use pyo3::prelude::*;


#[pymodule]
fn pyfast(_py: Python<'_>, m: &PyModule) -> PyResult<()>  {

    m.add_class::<cache::backend::BaseBackend>()?;
    m.add_class::<cache::redis_backend::RedisBackend>()?;

    m.add_class::<openapi::schemas::BaseSchemaGenerator>()?;
    m.add_class::<openapi::swagger::SwaggerUI>()?;    

    m.add_class::<background::background_task::BackgroundTask>()?;
    m.add_class::<background::background_tasks::BackgroundTasks>()?;

    pyo3::prepare_freethreaded_python();
    Ok(())
}
