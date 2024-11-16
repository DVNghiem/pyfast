use pyo3::prelude::*;

use super::route::Route;

/// Contains the thread safe hashmaps of different routes
#[pyclass]
#[derive(Debug, Default)]
pub struct Router {
    #[pyo3(get, set)]
    path: String,

    #[pyo3(get, set)]
    routes: Vec<Route>,
}

#[pymethods]
impl Router {
    #[new]
    fn new(path: &str) -> Self {
        Self {
            path: path.to_string(),
            routes: Vec::new(),
        }
    }

    /// Add a new route to the router
    pub fn add_route(&mut self, route: Route) {
        self.routes.push(route);
    }
}

impl Router {
    pub fn iter(&self) -> std::slice::Iter<Route> {
        self.routes.iter()
    }

}
