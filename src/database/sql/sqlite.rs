use std::sync::Arc;

use super::db_trait::{DatabaseOperations, DynamicParameterBinder};
use futures::StreamExt;
use pyo3::{prelude::*, types::PyDict};
use sqlx::{
    query::Query,
    sqlite::{SqliteArguments, SqliteRow},
    Column, Row, Sqlite, ValueRef,
};
use tokio::sync::Mutex;

pub struct SqliteParameterBinder;

impl DynamicParameterBinder for SqliteParameterBinder {
    type Arguments = SqliteArguments<'static>;
    type Database = Sqlite;
    type Row = SqliteRow;

    fn bind_parameters<'q>(
        &self,
        mut query: Query<'q, Sqlite, SqliteArguments<'q>>,
        params: Vec<&PyAny>,
    ) -> Result<Query<'q, Self::Database, Self::Arguments>, PyErr> {
        // Box the query string to give it a 'static lifetime

        // Bind parameters dynamically
        for param in params {
            query = if let Ok(s) = param.extract::<String>() {
                query.bind(s)
            } else if let Ok(i) = param.extract::<i64>() {
                query.bind(i)
            } else if let Ok(f) = param.extract::<f64>() {
                query.bind(f)
            } else if let Ok(b) = param.extract::<bool>() {
                query.bind(b)
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                    "Unsupported parameter type: {:?}",
                    param.get_type()
                )));
            };
        }

        // Transmute to 'static lifetime (safe because we've boxed the string)
        // This is a bit of a hack, but necessary to satisfy the lifetime requirements
        unsafe { std::mem::transmute(query) }
    }

    fn bind_result(&self, py: Python<'_>, row: &SqliteRow) -> Result<PyObject, PyErr> {
        let dict = PyDict::new(py);

        for (i, column) in row.columns().iter().enumerate() {
            let column_name = column.name();

            // Dynamically handle different column types
            match row.try_get_raw(i) {
                Ok(val) => {
                    if val.is_null() {
                        dict.set_item(column_name, py.None())?;
                    } else if let Ok(int_val) = row.try_get::<i32, _>(i) {
                        dict.set_item(column_name, int_val)?;
                    } else if let Ok(float_val) = row.try_get::<f64, _>(i) {
                        dict.set_item(column_name, float_val)?;
                    } else if let Ok(bool_val) = row.try_get::<bool, _>(i) {
                        dict.set_item(column_name, bool_val)?;
                    } else if let Ok(string_val) = row.try_get::<String, _>(i) {
                        dict.set_item(column_name, string_val)?;
                    } else {
                        return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                            "Unsupported column type: {:?}",
                            val.type_info()
                        )));
                    }
                }
                Err(e) => {
                    return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        e.to_string(),
                    ))
                }
            }
        }

        Ok(dict.into())
    }
}

#[derive(Debug, Clone, Default)]
#[pyclass]
pub struct SqliteDatabase;

impl DatabaseOperations for SqliteDatabase {
    type Row = SqliteRow;
    type Arguments = SqliteArguments<'static>;
    type DatabaseType = sqlx::Sqlite;
    type ParameterBinder = SqliteParameterBinder;

    async fn execute(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Sqlite>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<u64, PyErr> {
        let query = sqlx::query(Box::leak(query.to_string().into_boxed_str()));
        let query_builder = SqliteParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await.take().unwrap();
        let result = query_builder
            .execute(&mut *guard)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(result.rows_affected())
    }

    async fn fetch_all(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr> {
        let query = sqlx::query(Box::leak(query.to_string().into_boxed_str()));
        let query_builder = SqliteParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await;
        let transaction = guard.as_mut().unwrap();
        let rows = query_builder
            .fetch_all(&mut **transaction)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let result: Vec<PyObject> = rows
            .iter()
            .map(|row| SqliteParameterBinder.bind_result(py, row))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(result)
    }

    async fn stream_data(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Sqlite>>>>,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>> {
        let query = sqlx::query(Box::leak(query.to_string().into_boxed_str()));
        let query_builder = SqliteParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await.take().unwrap();
        let mut stream = query_builder.fetch(&mut *guard);
        let mut chunks: Vec<Vec<PyObject>> = Vec::new();
        let mut current_chunk: Vec<PyObject> = Vec::new();

        while let Some(row_result) = stream.next().await {
            match row_result {
                Ok(row) => {
                    let row_data: PyObject = SqliteParameterBinder.bind_result(py, &row)?;
                    current_chunk.push(row_data);

                    if current_chunk.len() >= chunk_size {
                        chunks.push(current_chunk);
                        current_chunk = Vec::new();
                    }
                }
                Err(e) => {
                    return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        e.to_string(),
                    ));
                }
            }
        }

        if !current_chunk.is_empty() {
            chunks.push(current_chunk);
        }
        Ok(chunks)
    }

    async fn bulk_change(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<Vec<&PyAny>>,
        batch_size: usize,
    ) -> Result<u64, PyErr> {
        let mut total_affected: u64 = 0;
        let mut guard = transaction.lock().await;
        let tx = guard.as_mut().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("No active transaction")
        })?;

        // Process in batches
        for chunk in params.chunks(batch_size) {
            for param_set in chunk {
                // Build query with current parameters
                let mut query_builder = sqlx::query(Box::leak(query.to_string().into_boxed_str()));
                for param in param_set {
                    query_builder =
                        SqliteParameterBinder.bind_parameters(query_builder, vec![*param])?;
                }
                // Execute query and accumulate affected rows
                let result = query_builder.execute(&mut **tx).await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string())
                })?;

                total_affected += result.rows_affected();
            }
        }
        Ok(total_affected)
    }
}
