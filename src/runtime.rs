
use tokio::runtime::Runtime;

use once_cell::sync::OnceCell;

static RUNTIME: OnceCell<Runtime> = OnceCell::new();

pub fn get_runtime() -> &'static Runtime {
    RUNTIME.get_or_init(|| Runtime::new().unwrap())
}



