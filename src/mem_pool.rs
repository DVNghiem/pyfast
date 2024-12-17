use parking_lot::RwLock;
use pyo3::{prelude::*, types::PyDict};
use std::{
    collections::VecDeque,
    sync::Arc,
    time::{Duration, Instant},
};
struct PoolMetrics {
    last_access: Instant,
    hit_count: u64,
    miss_count: u64,
}

struct PoolItem {
    object: PyObject,
    last_used: Instant,
}

pub struct AdaptiveMemoryPool {
    pool: Arc<RwLock<VecDeque<PoolItem>>>,
    metrics: Arc<RwLock<PoolMetrics>>,
    min_capacity: usize,
    max_capacity: usize,
    cleanup_interval: Duration,
    retention_period: Duration,
    last_cleanup: Arc<RwLock<Instant>>,
}

impl AdaptiveMemoryPool {
    pub fn new(min_capacity: usize, max_capacity: usize) -> Self {
        let pool = Self {
            pool: Arc::new(RwLock::new(VecDeque::with_capacity(min_capacity))),
            metrics: Arc::new(RwLock::new(PoolMetrics {
                last_access: Instant::now(),
                hit_count: 0,
                miss_count: 0,
            })),
            min_capacity,
            max_capacity,
            cleanup_interval: Duration::from_secs(300), // 5 minutes
            retention_period: Duration::from_secs(3600), // 1 hour
            last_cleanup: Arc::new(RwLock::new(Instant::now())),
        };

        // Start background cleanup task
        pool.start_cleanup_task();
        pool
    }

    pub fn get_dict(&self, py: Python) -> PyResult<PyObject> {
        self.maybe_cleanup();

        let mut pool = self.pool.write();
        let mut metrics = self.metrics.write();
        metrics.last_access = Instant::now();

        // Try to find a reusable dict from the pool
        while let Some(item) = pool.pop_front() {
            if item.last_used.elapsed() < self.retention_period {
                metrics.hit_count += 1;
                return Ok(item.object.as_ref(py).downcast::<PyDict>()?.into());
            }
        }

        // If no reusable dict found, create new one
        metrics.miss_count += 1;
        Ok(PyDict::new(py).into())
    }

    pub fn return_dict(&self, py: Python, dict: PyObject) {
        let mut pool = self.pool.write();

        // Check if we should expand capacity
        let current_capacity = pool.capacity();
        let usage_ratio = pool.len() as f64 / current_capacity as f64;

        if usage_ratio > 0.8 && current_capacity < self.max_capacity {
            // Increase capacity by 25% but not exceeding max_capacity
            let new_capacity = (current_capacity * 5 / 4).min(self.max_capacity);
            pool.reserve(new_capacity - current_capacity);
        }

        dict.as_ref(py).downcast::<PyDict>().unwrap().clear();  

        pool.push_back(PoolItem {
            object: dict,
            last_used: Instant::now(),
        });
    }

    fn maybe_cleanup(&self) {
        let mut last_cleanup = self.last_cleanup.write();
        if last_cleanup.elapsed() >= self.cleanup_interval {
            self.cleanup();
            *last_cleanup = Instant::now();
        }
    }

    fn cleanup(&self) {
        let mut pool = self.pool.write();
        let metrics = self.metrics.read();
        // Remove old items
        pool.retain(|item| item.last_used.elapsed() < self.retention_period);

        // Check if we should reduce capacity
        let current_capacity = pool.capacity();
        if current_capacity > self.min_capacity {
            // Calculate usage metrics
            let hit_ratio =
                metrics.hit_count as f64 / (metrics.hit_count + metrics.miss_count) as f64;
            let time_since_last_access = metrics.last_access.elapsed();

            // Reduce capacity if pool is underutilized
            if hit_ratio < 0.5 || time_since_last_access > Duration::from_secs(1800) {
                let new_capacity = (current_capacity * 3 / 4).max(self.min_capacity);
                pool.shrink_to(new_capacity);
            }
        }
    }

    fn start_cleanup_task(&self) {
        let pool = Arc::clone(&self.pool);
        let metrics = Arc::clone(&self.metrics);
        let cleanup_interval = self.cleanup_interval;
        let retention_period = self.retention_period;
        let min_capacity = self.min_capacity;

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(cleanup_interval);
            loop {
                interval.tick().await;

                let mut pool = pool.write();
                let metrics = metrics.read();

                // Remove expired items 
                pool.retain(|item| item.last_used.elapsed() < retention_period);

                // Adjust capacity based on usage patterns
                let current_capacity = pool.capacity();
                if current_capacity > min_capacity {
                    let hit_ratio =
                        metrics.hit_count as f64 / (metrics.hit_count + metrics.miss_count) as f64;
                    let time_since_last_access = metrics.last_access.elapsed();

                    if hit_ratio < 0.5 || time_since_last_access > Duration::from_secs(1800) {
                        let new_capacity = (current_capacity * 3 / 4).max(min_capacity);
                        pool.shrink_to(new_capacity);
                    }
                }
            }
        });
    }

}
