use std::sync::Arc;
use tokio::sync::Mutex;

use futures::StreamExt;
use pyo3::{prelude::*, types::PyDict};
use sqlx::{
    mysql::{MySqlArguments, MySqlRow},
    Column, Row, ValueRef,
};

use super::db_trait::{DatabaseOperations, DynamicParameterBinder};
// Similarly implement for other database types...
pub struct MySqlParameterBinder;

impl DynamicParameterBinder for MySqlParameterBinder {
    type Arguments = MySqlArguments;
    type Database = sqlx::MySql;
    type Row = MySqlRow;

    fn bind_parameters<'q>(
        &self,
        query: &'q str,
        params: Vec<&PyAny>,
    ) -> Result<sqlx::query::Query<'q, Self::Database, Self::Arguments>, PyErr> {
        // Create query with explicit lifetime
        let mut query_builder = sqlx::query::<Self::Database>(query);

        // Bind parameters with lifetime preservation
        for param in params {
            query_builder = match param.extract::<String>() {
                // Use String instead of &str
                Ok(s) => query_builder.bind(s),
                Err(_) => match param.extract::<i64>() {
                    Ok(i) => query_builder.bind(i),
                    Err(_) => match param.extract::<f64>() {
                        Ok(f) => query_builder.bind(f),
                        Err(_) => match param.extract::<bool>() {
                            Ok(b) => query_builder.bind(b),
                            Err(_) => {
                                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                                    format!("Unsupported parameter type: {:?}", param.get_type()),
                                ))
                            }
                        },
                    },
                },
            };
        }

        Ok(query_builder)
    }

    fn bind_result(&self, py: Python<'_>, row: &MySqlRow) -> Result<PyObject, PyErr> {
        let dict = PyDict::new(py);

        for (i, column) in row.columns().iter().enumerate() {
            let column_name = column.name();

            // Dynamically handle different column types
            match row.try_get_raw(i) {
                Ok(val) => {
                    if val.is_null() {
                        dict.set_item(column_name, py.None()).unwrap();
                    } else if let Ok(int_val) = row.try_get::<i32, _>(i) {
                        dict.set_item(column_name, int_val).unwrap();
                    } else if let Ok(str_val) = row.try_get::<String, _>(i) {
                        dict.set_item(column_name, str_val).unwrap();
                    } else if let Ok(float_val) = row.try_get::<f64, _>(i) {
                        dict.set_item(column_name, float_val).unwrap();
                    } else if let Ok(bool_val) = row.try_get::<bool, _>(i) {
                        dict.set_item(column_name, bool_val).unwrap();
                    }
                }
                Err(_) => {
                    // Handle unsupported types or log an error
                    dict.set_item(column_name, py.None()).unwrap();
                }
            }
        }

        Ok(dict.into())
    }
}

#[derive(Debug, Clone, Default)]
pub struct MySqlDatabase;

impl DatabaseOperations for MySqlDatabase {
    type Row = MySqlRow;
    type Arguments = MySqlArguments;
    type DatabaseType = sqlx::MySql;
    type ParameterBinder = MySqlParameterBinder;

    async fn execute(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::MySql>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<u64, PyErr> {
        let parameter_binder = MySqlParameterBinder;
        let query_builder = parameter_binder.bind_parameters(query, params)?;
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
        let parameter_binder = MySqlParameterBinder;
        let query_builder = parameter_binder.bind_parameters(query, params)?;
        let mut guard  = transaction.lock().await;
        let transaction = guard.as_mut().unwrap();
        let rows = query_builder
            .fetch_all(&mut **transaction)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let result: Vec<PyObject> = rows
            .iter()
            .map(|row| parameter_binder.bind_result(py, row))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(result)
    }

    async fn stream_data(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::MySql>>>>,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>> {
        let parameter_binder = MySqlParameterBinder;
        let query_builder = parameter_binder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await.take().unwrap();
        let mut stream = query_builder.fetch(&mut *guard);
        let mut chunks: Vec<Vec<PyObject>> = Vec::new();
        let mut current_chunk: Vec<PyObject> = Vec::new();

        while let Some(row_result) = stream.next().await {
            match row_result {
                Ok(row) => {
                    let row_data: PyObject = parameter_binder.bind_result(py, &row)?;
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
}
