
use pyo3::prelude::*;
use crate::types::function_info::FunctionInfo;

#[derive(Clone)]
#[pyclass]
pub struct Middleware {
    before_hooks: Vec<FunctionInfo>,
    after_hooks: Vec<FunctionInfo>,
}

impl Middleware {
    pub fn new() -> PyResult<Self> {
        let before_hooks = Vec::new();
        let after_hooks = Vec::new();
        Ok(Self {
            before_hooks,
            after_hooks,
        })
    }

    pub fn add_before_hook(&mut self, hook: FunctionInfo) {
        self.before_hooks.push(hook);
    }

    pub fn add_after_hook(&mut self, hook: FunctionInfo) {
        self.after_hooks.push(hook);
    }

    pub fn get_before_hooks(&self) -> Vec<FunctionInfo> {
        self.before_hooks.clone()
    }

    pub fn get_after_hooks(&self,) ->Vec<FunctionInfo> {
        self.after_hooks.clone()
    }

    pub fn set_before_hooks(&mut self, hooks: Vec<FunctionInfo>) {
        self.before_hooks = hooks;
    }

    pub fn set_after_hooks(&mut self, hooks: Vec<FunctionInfo>) {
        self.after_hooks = hooks;
    }
}
