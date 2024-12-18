use std::sync::Arc;

use chrono::{Datelike, NaiveDate, NaiveDateTime, NaiveTime, Timelike};
use futures::StreamExt;
use pyo3::{
    prelude::*,
    types::{
        PyBool, PyDate, PyDateAccess, PyDateTime, PyDict, PyFloat, PyInt, PyList, PyString, PyTime,
        PyTimeAccess,
    },
};
use serde_json::to_string;
use sqlx::{
    postgres::{PgArguments, PgRow},
    types::{Json, JsonValue},
    Column, Row, ValueRef,
};
use tokio::sync::Mutex;

use super::db_trait::{DatabaseOperations, DynamicParameterBinder};
// Similarly implement for other database types...
pub struct PostgresParameterBinder;

impl DynamicParameterBinder for PostgresParameterBinder {
    type Arguments = PgArguments;
    type Database = sqlx::Postgres;
    type Row = PgRow;


    fn convert_sql_params<'q>(
        &self,
        _query: &str,
        _params: Vec<&'q PyAny>,
    ) -> Result<(String, Vec<&'q PyAny>), PyErr> {
        todo!()
    }


    fn bind_parameters<'q>(
        &self,
        query: &'q str,
        params: Vec<&PyAny>,
    ) -> Result<sqlx::query::Query<'q, Self::Database, PgArguments>, PyErr> {

        let mut query_builder = sqlx::query(query);

        for param in params {
            query_builder = match param {
                // Primitive Types
                p if p.is_none() => query_builder.bind(None::<Option<String>>),
                p if p.is_instance_of::<PyString>() => query_builder.bind(p.extract::<String>()?),
                p if p.is_instance_of::<PyInt>() => query_builder.bind(p.extract::<i64>()?),
                p if p.is_instance_of::<PyFloat>() => query_builder.bind(p.extract::<f64>()?),
                p if p.is_instance_of::<PyBool>() => query_builder.bind(p.extract::<bool>()?),

                // DateTime Types
                p if p.is_instance_of::<PyDateTime>() => {
                    let dt: &PyDateTime = p.downcast()?;
                    let naive_dt = NaiveDateTime::new(
                        NaiveDate::from_ymd_opt(
                            dt.get_year(),
                            dt.get_month() as u32,
                            dt.get_day() as u32,
                        )
                        .unwrap(),
                        NaiveTime::from_hms_nano_opt(
                            dt.get_hour() as u32,
                            dt.get_minute() as u32,
                            dt.get_second() as u32,
                            dt.get_microsecond() as u32 * 1000,
                        )
                        .unwrap(),
                    );
                    query_builder.bind(naive_dt)
                }
                p if p.is_instance_of::<PyDate>() => {
                    let date: &PyDate = p.downcast()?;
                    let naive_date = NaiveDate::from_ymd_opt(
                        date.get_year(),
                        date.get_month() as u32,
                        date.get_day() as u32,
                    )
                    .unwrap();
                    query_builder.bind(naive_date)
                }
                p if p.is_instance_of::<PyTime>() => {
                    let time: &PyTime = p.downcast()?;
                    let naive_time = NaiveTime::from_hms_nano_opt(
                        time.get_hour() as u32,
                        time.get_minute() as u32,
                        time.get_second() as u32,
                        time.get_microsecond() as u32 * 1000,
                    )
                    .unwrap();
                    query_builder.bind(naive_time)
                }

                // JSONB Support
                p if p.is_instance_of::<PyDict>() => {
                    let dict: &PyDict = p.downcast()?;
                    let json_value: JsonValue =
                        serde_json::from_str(&dict.to_string()).unwrap_or(JsonValue::Null);
                    query_builder.bind(Json(json_value))
                }
                p if p.is_instance_of::<PyList>() => {
                    let list: &PyList = p.downcast()?;
                    let json_value: JsonValue =
                        serde_json::from_str(&list.to_string()).unwrap_or(JsonValue::Null);
                    query_builder.bind(Json(json_value))
                }

                // Fallback for unsupported types
                _ => {
                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                        "Unsupported parameter type: {:?}",
                        param.get_type()
                    )))
                }
            };
        }

        Ok(query_builder)
    }

    fn bind_result(&self, py: Python<'_>, row: &PgRow) -> Result<PyObject, PyErr> {
        let dict = PyDict::new(py);

        for (i, column) in row.columns().iter().enumerate() {
            let column_name = column.name();

            // Dynamically handle different column types
            match row.try_get_raw(i) {
                Ok(val) => {
                    if val.is_null() {
                        dict.set_item(column_name, py.None())?;
                    } else {
                        // Primitive Types
                        if let Ok(int_val) = row.try_get::<i32, _>(i) {
                            dict.set_item(column_name, int_val)?;
                        } else if let Ok(bigint_val) = row.try_get::<i64, _>(i) {
                            dict.set_item(column_name, bigint_val)?;
                        } else if let Ok(str_val) = row.try_get::<String, _>(i) {
                            dict.set_item(column_name, str_val)?;
                        } else if let Ok(float_val) = row.try_get::<f64, _>(i) {
                            dict.set_item(column_name, float_val)?;
                        } else if let Ok(bool_val) = row.try_get::<bool, _>(i) {
                            dict.set_item(column_name, bool_val)?;
                        }
                        // Date and Time Types
                        else if let Ok(datetime_val) = row.try_get::<NaiveDateTime, _>(i) {
                            let py_datetime = PyDateTime::new(
                                py,
                                datetime_val.year(),
                                datetime_val.month() as u8,
                                datetime_val.day() as u8,
                                datetime_val.hour() as u8,
                                datetime_val.minute() as u8,
                                datetime_val.second() as u8,
                                (datetime_val.nanosecond() / 1000) as u32,
                                None,
                            )?;
                            dict.set_item(column_name, py_datetime)?;
                        } else if let Ok(date_val) = row.try_get::<NaiveDate, _>(i) {
                            let py_date = PyDate::new(
                                py,
                                date_val.year(),
                                date_val.month() as u8,
                                date_val.day() as u8,
                            )?;
                            dict.set_item(column_name, py_date)?;
                        } else if let Ok(time_val) = row.try_get::<NaiveTime, _>(i) {
                            let py_time = PyTime::new(
                                py,
                                time_val.hour() as u8,
                                time_val.minute() as u8,
                                time_val.second() as u8,
                                (time_val.nanosecond() / 1000) as u32,
                                None,
                            )?;
                            dict.set_item(column_name, py_time)?;
                        }
                        // JSONB and Complex Types
                        else if let Ok(json_val) = row.try_get::<Json<JsonValue>, _>(i) {
                            // Convert JSON to Python object
                            let json_str = to_string(&json_val.0).map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                            })?;

                            // let py_json =
                            //     py.eval(&format!("import orjson; orjson.loads('{}')", json_str), None, None)?;
                            dict.set_item(column_name, json_str)?;
                        }
                        // Array Types (basic support)
                        else if let Ok(str_array) = row.try_get::<Vec<String>, _>(i) {
                            let py_list = PyList::new(py, &str_array);
                            dict.set_item(column_name, py_list)?;
                        } else if let Ok(int_array) = row.try_get::<Vec<i32>, _>(i) {
                            let py_list = PyList::new(py, &int_array);
                            dict.set_item(column_name, py_list)?;
                        }
                        // Fallback for unknown types
                        else {
                            dict.set_item(column_name, py.None())?;
                        }
                    }
                }
                Err(_) => {
                    // Handle any retrieval errors
                    dict.set_item(column_name, py.None())?;
                }
            }
        }

        Ok(dict.into())
    }
}

#[derive(Debug, Clone, Default)]
pub struct PostgresDatabase;

impl DatabaseOperations for PostgresDatabase {
    type Row = PgRow;
    type Arguments = sqlx::postgres::PgArguments;
    type DatabaseType = sqlx::Postgres;
    type ParameterBinder = PostgresParameterBinder;

    async fn execute(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Postgres>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<u64, PyErr> {
        let query_builder = PostgresParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await;
        let transaction = guard.as_mut().unwrap();
        let result = query_builder
            .execute(&mut **transaction)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        std::mem::drop(guard);
        Ok(result.rows_affected())
    }

    async fn fetch_all(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, Self::DatabaseType>>>>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr> {

        let query_builder = PostgresParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await;
        let transaction = guard.as_mut().unwrap();
        let rows = query_builder
            .fetch_all(&mut **transaction)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let result: Vec<PyObject> = rows
            .iter()
            .map(|row| PostgresParameterBinder.bind_result(py, row))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(result)
    }

    async fn stream_data(
        &mut self,
        py: Python<'_>,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Postgres>>>>,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>> {
        let query_builder = PostgresParameterBinder.bind_parameters(query, params)?;
        let mut guard = transaction.lock().await.take().unwrap();
        let mut stream = query_builder.fetch(&mut *guard);
        let mut chunks: Vec<Vec<PyObject>> = Vec::new();
        let mut current_chunk: Vec<PyObject> = Vec::new();

        while let Some(row_result) = stream.next().await {
            match row_result {
                Ok(row) => {
                    let row_data: PyObject = PostgresParameterBinder.bind_result(py, &row)?;
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
                let query_builder = PostgresParameterBinder.bind_parameters(query, param_set.to_vec())?;
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
