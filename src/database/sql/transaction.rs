use std::sync::Arc;

use pyo3::{exceptions::PyException, prelude::*};
use tokio::sync::Mutex;

use crate::utils::get_db_runtime;

use super::{
    db_trait::DatabaseOperations, mysql::MySqlDatabase, postgresql::PostgresDatabase,
    sqlite::SqliteDatabase,
};

#[derive(Debug, Clone)]
pub enum DatabaseTransactionType {
    Sqlite(
        SqliteDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Sqlite>>>>,
    ),
    Postgres(
        PostgresDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Postgres>>>>,
    ),
    MySql(
        MySqlDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::MySql>>>>,
    ),
}

#[pyclass]
pub struct DatabaseTransaction {
    transaction: DatabaseTransactionType,
}

impl DatabaseTransaction {
    pub fn from_transaction(transaction: DatabaseTransactionType) -> Self {
        Self {
            transaction,
        }
    }
}

#[pymethods]
impl DatabaseTransaction {
    fn execute(&self, query: &str, params: Vec<&PyAny>) -> PyResult<u64> {
        let transaction = self.transaction.clone();
        let result = get_db_runtime().block_on(async move {
            match transaction {
                DatabaseTransactionType::Sqlite(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                }
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                } // Add other database types
            }
        })?;

        Ok(result)
    }

    fn fetch_all(
        &self,
        py: Python<'_>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr> {
        let transaction = self.transaction.clone();
        let result = get_db_runtime().block_on(async move {
            match transaction {
                DatabaseTransactionType::Sqlite(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                } // Add other database types
            }
        })?;

        Ok(result)
    }

    fn stream_data(
        &self,
        py: Python<'_>,
        query: &str,
        params: Vec<&PyAny>,
        chunk_size: usize,
    ) -> PyResult<Vec<Vec<PyObject>>> {
        let result = get_db_runtime().block_on(async move {
            let transaction = self.transaction.clone();
            match transaction {
                DatabaseTransactionType::Sqlite(mut db, transaction) => {
                    db.stream_data(py, transaction, query, params, chunk_size)
                        .await
                }
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.stream_data(py, transaction, query, params, chunk_size)
                        .await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.stream_data(py, transaction, query, params, chunk_size)
                        .await
                } // Add other database types
            }
        })?;

        Ok(result)
    }

    fn commit(&self) -> PyResult<()> {
        let result = get_db_runtime().block_on(async move {
            match &self.transaction {
                DatabaseTransactionType::Sqlite(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::Postgres(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
            }
        });
    
        result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
        Ok(())
    }

    fn rollback(&self) -> PyResult<()> {
        let result = get_db_runtime().block_on(async move {
            match &self.transaction {
                DatabaseTransactionType::Sqlite(_, transaction) => {
                    transaction.lock().await.take().unwrap().rollback().await
                }
                DatabaseTransactionType::Postgres(_, transaction) => {
                    transaction.lock().await.take().unwrap().rollback().await
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    transaction.lock().await.take().unwrap().rollback().await
                }
            }
        });
    
        result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
        Ok(())
    }

    fn __del__(&self) {
        let _ = get_db_runtime().block_on(async move {
            match &self.transaction {
                DatabaseTransactionType::Sqlite(_, transaction) => {
                    if let Some(transaction) = transaction.lock().await.take() {
                        transaction.rollback().await.ok();
                    }
                }
                DatabaseTransactionType::Postgres(_, transaction) => {
                    if let Some(transaction) = transaction.lock().await.take() {
                        transaction.rollback().await.ok();
                    }
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    if let Some(transaction) = transaction.lock().await.take() {
                        transaction.rollback().await.ok();
                    }
                }
            }
        });
    }

    fn __enter__(&self) -> PyResult<()> {
        Ok(())
    }

    fn __exit__(&self, _exc_type: PyObject, _exc_value: PyObject, _traceback: PyObject) -> PyResult<()> {
        let result = get_db_runtime().block_on(async move {
            match &self.transaction {
                DatabaseTransactionType::Sqlite(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::Postgres(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
            }
        });
    
        result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
        Ok(())
    }
}
