use std::sync::Arc;

use pyo3::prelude::*;
use sqlx::Database;
use tokio::sync::Mutex;

// Trait for dynamic parameter binding
pub trait DynamicParameterBinder {
    type Arguments;
    type Database: Database;
    type Row;

    fn convert_sql_params<'q>(
        &self,
        query: &str,
        params: Vec<&'q PyAny>,
    ) -> Result<(String, Vec<&'q PyAny>), PyErr>;

    fn bind_parameters<'q>(
        &self,
        query: &'q str,
        params: Vec<&PyAny>,
    ) -> Result<sqlx::query::Query<'q, Self::Database, Self::Arguments>, PyErr>;

    fn bind_result(&self, py: Python<'_>, row: &Self::Row) -> Result<PyObject, PyErr>;
}

// Base trait for database operations with dynamic parameters
pub trait DatabaseOperations {
    type Row;
    type Arguments;
    type DatabaseType: Database;
    type ParameterBinder: DynamicParameterBinder<
        Arguments = Self::Arguments,
        Database = Self::DatabaseType,
    >;

    async fn execute(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<u64, PyErr>;

    async fn fetch_all(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr>;

    async fn stream_data(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>>;

    async fn bulk_change(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<Vec<&PyAny>>,
        batch_size: usize,
    ) -> Result<u64, PyErr>;
}
