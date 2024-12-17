use once_cell::sync::OnceCell;
use tokio::runtime::Runtime;

use crate::mem_pool::AdaptiveMemoryPool;

static RUNTIME: OnceCell<Runtime> = OnceCell::new();
static MEM_POOL: OnceCell<AdaptiveMemoryPool> = OnceCell::new();

pub fn get_runtime() -> &'static Runtime {
    RUNTIME.get_or_init(|| Runtime::new().unwrap())
}

pub fn create_mem_pool(min_capacity: usize, max_capacity: usize) {
    let pool = AdaptiveMemoryPool::new(min_capacity, max_capacity);
    match MEM_POOL.set(pool) {
        Ok(_) => (),
        Err(_) => panic!("Memory pool already initialized"),
    };
}

pub fn get_mem_pool() -> &'static AdaptiveMemoryPool {
    MEM_POOL.get_or_init(|| AdaptiveMemoryPool::new(10, 100))
}
