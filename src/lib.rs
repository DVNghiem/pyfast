mod cache;
mod endpoint;
use pyo3::prelude::*;


#[pymodule]
fn pyfast(m: &Bound<'_, PyModule>) -> PyResult<()> {

    let cache_module = PyModule::new_bound(m.py(), "cache")?;
    cache_module.add_class::<cache::backend::BaseBackend>()?;
    cache_module.add_class::<cache::redis_backend::RedisBackend>()?;

    m.add_submodule(&cache_module)?;

    pyo3::prepare_freethreaded_python();
    Ok(())
}
