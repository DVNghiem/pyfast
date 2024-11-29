use parking_lot::Mutex;
use std::sync::Arc;
use std::sync::OnceLock;
use tokio::runtime::Runtime;

pub struct RuntimeManager {
    runtime: Arc<Runtime>,
}

impl RuntimeManager {
    pub fn new() -> Self {
        Self {
            runtime: Arc::new(tokio::runtime::Runtime::new().unwrap()),
        }
    }

    pub fn global() -> &'static Self {
        static INSTANCE: OnceLock<RuntimeManager> = OnceLock::new();
        INSTANCE.get_or_init(|| RuntimeManager::new())
    }

    pub fn block_on<F, R>(&self, future: F) -> R
    where
        F: std::future::Future<Output = R>,
    {
        let runtime_guard = self.runtime.clone();
        runtime_guard.handle().block_on(future)
    }

}
