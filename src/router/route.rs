use pyo3::prelude::*;
use crate::types::function_info::FunctionInfo;

#[pyclass]
#[derive(Debug, Clone)]
pub struct Route {
    #[pyo3(get, set)]
    pub path: String,

    #[pyo3(get, set)]
    pub function: FunctionInfo,

    #[pyo3(get, set)]
    pub method: String,
}

#[pymethods]
impl Route {
    #[new]
    pub fn new(path: &str, function: FunctionInfo, method: String) -> Self {
        Self {
            path: path.to_string(),
            function,
            method
        }
    }

    // Get a formatted string representation of the route
    pub fn __str__(&self) -> PyResult<String> {
        Ok(format!("{} {}", self.method, self.path))
    }

    // Get a formatted representation for debugging
    pub fn __repr__(&self) -> PyResult<String> {
        Ok(format!("Route(path='{}', method='{}')", 
            self.path, self.method))
    }

    // Check if route matches given path and method
    pub fn matches(&self, path: &str, method: &str) -> bool {
        self.path == path && self.method.to_uppercase() == method.to_uppercase()
    }

    // Create a copy of the route
    pub fn clone_route(&self) -> Route {
        self.clone()
    }

    // Update the route path
    pub fn update_path(&mut self, new_path: &str) {
        self.path = new_path.to_string();
    }

    // Update the route method
    pub fn update_method(&mut self, new_method: &str) {
        self.method = new_method.to_uppercase();
    }

    // Validate if the route configuration is correct
    pub fn is_valid(&self) -> bool {
        // Path should start with '/'
        if !self.path.starts_with('/') {
            return false;
        }

        // Method should be a valid HTTP method
        let valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"];
        if !valid_methods.contains(&self.method.to_uppercase().as_str()) {
            return false;
        }

        true
    }

    // Get route parameters from path
    pub fn get_path_params(&self) -> Vec<String> {
        self.path
            .split('/')
            .filter(|segment| segment.starts_with(':'))
            .map(|param| param[1..].to_string())
            .collect()
    }

    // Check if route has path parameters
    pub fn has_parameters(&self) -> bool {
        self.path.contains(':')
    }

    // Generate a normalized version of the path
    pub fn normalized_path(&self) -> String {
        // Remove trailing slashes and ensure leading slash
        let mut path = self.path.trim_end_matches('/').to_string();
        if !path.starts_with('/') {
            path = format!("/{}", path);
        }
        path
    }

    // Compare routes for equality based only on path and method
    fn __eq__(&self, other: &PyAny) -> PyResult<bool> {
        // Try to extract other as Route
        if let Ok(other_route) = other.extract::<PyRef<Route>>() {
            // Compare only path and method, not the function
            Ok(self.path == other_route.path && 
               self.method.to_uppercase() == other_route.method.to_uppercase())
        } else {
            Ok(false)
        }
    }

    // Generate hash for the route based only on path and method
    fn __hash__(&self) -> PyResult<isize> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        self.path.hash(&mut hasher);
        self.method.to_uppercase().hash(&mut hasher);
        Ok(hasher.finish() as isize)
    }

    // Check if routes have the same handler function
    pub fn same_handler(&self, other: &Route) -> PyResult<bool> {
        // Compare the Python objects using the Python 'is' operator
        Ok(self.function.handler.is(&other.function.handler))
    }

    // Get method name for sorting and comparison
    pub fn get_method_priority(&self) -> u8 {
        match self.method.to_uppercase().as_str() {
            "GET" => 1,
            "POST" => 2,
            "PUT" => 3,
            "PATCH" => 4,
            "DELETE" => 5,
            "HEAD" => 6,
            "OPTIONS" => 7,
            _ => 99
        }
    }

    // Compare routes for sorting
    pub fn __lt__(&self, other: &PyAny) -> PyResult<bool> {
        if let Ok(other_route) = other.extract::<PyRef<Route>>() {
            // First compare by path length (shorter paths first)
            if self.path.len() != other_route.path.len() {
                return Ok(self.path.len() < other_route.path.len());
            }
            
            // Then by path string
            if self.path != other_route.path {
                return Ok(self.path < other_route.path);
            }
            
            // Finally by method priority
            Ok(self.get_method_priority() < other_route.get_method_priority())
        } else {
            Ok(false)
        }
    }
}