mod cache;
use pyo3::prelude::*;


#[pymodule]
fn pyfast(m: &Bound<'_, PyModule>) -> PyResult<()> {

    let cache_module = PyModule::new_bound(m.py(), "cache")?;
    cache_module.add_class::<cache::backend::BaseBackend>()?;

    m.add_submodule(&cache_module)?;
    Ok(())
}
