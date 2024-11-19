use pyo3::{prelude::*, types::PyDict};

use crate::{
    di::DependencyInjection,
    types::{function_info::FunctionInfo, request::Request, response::Response},
};

#[inline]
fn get_function_output<'a, T>(
    function: &'a FunctionInfo,
    py: Python<'a>,
    function_args: &T,
    deps: Option<DependencyInjection>,
) -> Result<&'a PyAny, PyErr>
where
    T: ToPyObject,
{
    let handler = function.handler.as_ref(py);
    let kwargs = PyDict::new(py);

    // Add dependencies to kwargs if provided
    if let Some(dependency_injection) = deps {
        let _ = kwargs.set_item(
            "inject",
            dependency_injection
                .to_object(py)
                .into_ref(py)
                .downcast::<PyDict>()?
                .to_owned(),
        );
    }
    handler.call((function_args.to_object(py),), Some(kwargs))
}

#[inline]
pub async fn execute_http_function(
    request: &Request,
    function: &FunctionInfo,
    deps: Option<DependencyInjection>,
) -> PyResult<Response> {
    if function.is_async {
        let output = Python::with_gil(|py| {
            let function_output = get_function_output(function, py, request, deps)?;
            pyo3_asyncio::tokio::into_future(function_output)
        })?
        .await?;

        return Python::with_gil(|py| -> PyResult<Response> { output.extract(py) });
    };

    Python::with_gil(|py| -> PyResult<Response> {
        get_function_output(function, py, request, deps)?.extract()
    })
}
