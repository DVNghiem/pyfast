use pyo3::prelude::*;
use sqlx::Database;

// Trait for dynamic parameter binding
pub trait DynamicParameterBinder {
    type Arguments;
    type Database: Database;
    type Row;

    fn bind_parameters<'q>(
        &self,
        query: &'q str,
        params: Vec<&PyAny>,
    ) -> Result<sqlx::query::Query<'q, Self::Database, Self::Arguments>, PyErr>;

    fn bind_result(&self, py: Python<'_>, row: &Self::Row) -> Result<PyObject, PyErr>;
}

// Base trait for database operations with dynamic parameters
pub trait DatabaseOperations {
    type Pool;
    type Row;
    type Arguments;
    type DatabaseType: Database;
    type ParameterBinder: DynamicParameterBinder<
        Arguments = Self::Arguments,
        Database = Self::DatabaseType,
    >;

    async fn execute(
        &self,
        pool: &Self::Pool,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<u64, PyErr>;

    async fn fetch_all(
        &self,
        py: Python<'_>,
        pool: &Self::Pool,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr>;

    async fn stream_data(
        &self,
        py: Python<'_>, 
        pool: &Self::Pool,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>>;
}
