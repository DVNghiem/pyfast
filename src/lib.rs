use pyo3::prelude::*;

mod utils;
mod cache;
mod openapi;
mod background;
mod scheduler;


#[pymodule]
fn hypern(_py: Python<'_>, m: &PyModule) -> PyResult<()>  {

    m.add_class::<cache::backend::BaseBackend>()?;
    m.add_class::<cache::redis_backend::RedisBackend>()?;

    m.add_class::<openapi::schemas::BaseSchemaGenerator>()?;
    m.add_class::<openapi::swagger::SwaggerUI>()?;    

    m.add_class::<background::background_task::BackgroundTask>()?;
    m.add_class::<background::background_tasks::BackgroundTasks>()?;

    m.add_class::<scheduler::scheduler::Scheduler>()?;

    pyo3::prepare_freethreaded_python();
    Ok(())
}
