use std::collections::HashMap;

use super::route::Route;

#[derive(Debug, Clone)]
pub struct RadixNode {
    path_segment: String,
    is_parameter: bool,
    children: HashMap<String, RadixNode>,
    route: Option<Route>,
}

impl RadixNode {
    pub fn new(segment: &str) -> Self {
        Self {
            path_segment: segment.to_string(),
            is_parameter: segment.starts_with(':'),
            children: HashMap::new(),
            route: None,
        }
    }
}

pub struct RadixTree {
    root: RadixNode,
}

impl RadixTree {
    pub fn new() -> Self {
        Self {
            root: RadixNode::new("/"),
        }
    }

    pub fn insert(&mut self, route: Route) {
        let path = route.normalized_path();
        let segments: Vec<&str> = path.split('/')
            .filter(|s| !s.is_empty())
            .collect();
        
        let mut current = &mut self.root;
        
        for segment in segments {
            current = current.children
                .entry(segment.to_string())
                .or_insert_with(|| RadixNode::new(segment));
        }
        
        current.route = Some(route);
    }

    pub fn find(&self, path: &str, method: &str) -> Option<Route> {
        let segments: Vec<&str> = path.split('/')
            .filter(|s| !s.is_empty())
            .collect();
        
        let mut current = &self.root;
        let mut params = HashMap::new();
        
        for segment in segments {
            let mut found = false;
            
            // Try exact match first
            if let Some(child) = current.children.get(segment) {
                current = child;
                found = true;
            }
            
            // Try parameter match if no exact match
            if !found {
                for child in current.children.values() {
                    if child.is_parameter {
                        params.insert(child.path_segment[1..].to_string(), segment.to_string());
                        current = child;
                        found = true;
                        break;
                    }
                }
            }
            
            if !found {
                return None;
            }
        }
        
        if let Some(route) = &current.route {
            if route.method.to_uppercase() == method.to_uppercase() {
                return Some(route.clone());
            }
        }
        
        None
    }
}