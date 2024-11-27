use std::sync::Arc;

use pyo3::prelude::*;
use tokio::sync::Mutex;
use sqlx::{Transaction, Sqlite, Executor};

use crate::utils::get_db_runtime;

use super::{
    db_trait::DatabaseOperations, mysql::MySqlDatabase, postgresql::PostgresDatabase,
    sqlite::SqliteDatabase,
};

#[derive(Debug, Clone)]
pub enum DatabaseTransactionType {
    Sqlite(
        SqliteDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::Sqlite>>>,
    ),
    Postgres(
        PostgresDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::Postgres>>>,
    ),
    MySql(
        MySqlDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::MySql>>>,
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
        let transaction = self.transaction.clone();
        get_db_runtime().block_on(async move {
            match transaction {
                DatabaseTransactionType::Sqlite(_, transaction) => {
                    let tx = transaction.lock().await;
                    tx.commit().await?;
                }
                DatabaseTransactionType::Postgres(_, transaction) => {
                    let tx = transaction.lock().await;
                    tx.commit().await?;
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    let tx = transaction.lock().await;
                    tx.commit().await?;
                }
            }
            Ok::<(), sqlx::Error>(())
        });
        Ok(())
    }
}
