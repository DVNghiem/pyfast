use crate::cache::backend::BaseBackend;
use pyo3::prelude::*;
use redis::{Client, Commands, Connection};

#[pyclass(extends=BaseBackend)]
pub struct RedisBackend {
    redis: Client,
}

#[pymethods]
impl RedisBackend {
    #[new]
    fn new(url: &str) -> (Self, BaseBackend) {
        let redis = Client::open(url).unwrap();
        (RedisBackend { redis }, BaseBackend::new())
    }

    pub fn get(&self, key: &str) -> PyResult<Option<String>> {
        let mut redis_conn: Connection = self.redis.get_connection().unwrap();
        let response: Option<String> = redis_conn.get(key).unwrap();
        Ok(response)
    }

    pub fn set(&self, response: String, key: String, ttl: i64) {
        let mut redis_conn: Connection = self.redis.get_connection().unwrap();
        let _: Result<String, redis::RedisError> = redis_conn.set(key.clone(), response);
        let _: Result<String, redis::RedisError> = redis_conn.expire(key, ttl);
    }

    pub fn delete_startswith(&self, value: String) {
        let mut redis_conn: Connection = self.redis.get_connection().unwrap();
        let keys: Vec<String> = redis_conn.keys(value).unwrap();
        for key in keys {
            let _: Result<String, redis::RedisError> = redis_conn.del(key);
        }
    }
}
