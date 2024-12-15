use pyo3::prelude::*;
use std::sync::Arc;
use tokio::sync::Mutex;

use crate::database::context::get_sql_connect;

use super::{
    db_trait::DatabaseOperations,
    postgresql::PostgresDatabase,
    mysql::MySqlDatabase,
    sqlite::SqliteDatabase,
};

#[derive(Debug, Clone)]
pub enum DatabaseTransactionType {
    Postgres(
        PostgresDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Postgres>>>>,
    ),
    MySql(
        MySqlDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::MySql>>>>,
    ),
    SQLite(
        SqliteDatabase,
        Arc<Mutex<Option<sqlx::Transaction<'static, sqlx::Sqlite>>>>,
    ),
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct DatabaseTransaction {
    transaction: DatabaseTransactionType,
}

impl DatabaseTransaction {
    pub fn from_transaction(transaction: DatabaseTransactionType) -> Self {
        Self { transaction }
    }

    pub async fn commit_internal<T>(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, T>>>>,
    ) where
        T: sqlx::Database,
    {
        let mut guard = transaction.lock().await;
        let transaction = guard.take().unwrap();
        transaction.commit().await.ok();

        match get_sql_connect() {
            Some(connection) => {
                let transaction = connection.begin_transaction().await;
                let pg = transaction
                    .unwrap()
                    .downcast::<sqlx::Transaction<'static, T>>()
                    .unwrap();
                guard.replace(*pg);
            }
            None => {}
        }
    }

    pub async fn rollback_internal<T>(
        &self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, T>>>>,
    ) where
        T: sqlx::Database,
    {
        let mut guard = transaction.lock().await;
        let transaction = guard.take().unwrap();
        transaction.rollback().await.ok();
    }
}

#[pymethods]
impl DatabaseTransaction {
    fn execute(&self, query: &str, params: Vec<&PyAny>) -> PyResult<u64> {
        let transaction = self.transaction.clone();
        let result = futures::executor::block_on(async move {
            match transaction {
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                }
                DatabaseTransactionType::SQLite(mut db, transaction) => {
                    db.execute(transaction, query, params).await
                }
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
        let result = futures::executor::block_on(async move {
            match self.transaction.clone() {
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    println!("====> {:?}", self);
                    db.fetch_all(py, transaction, query, params).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
                DatabaseTransactionType::SQLite(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
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
        let result = futures::executor::block_on(async move {
            match self.transaction.clone() {
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.stream_data(py, transaction, query, params, chunk_size)
                        .await
                } 
                DatabaseTransactionType::MySql(mut db, transaction) => {
                      db.stream_data(py, transaction, query, params, chunk_size)
                          .await
                  }
                  DatabaseTransactionType::SQLite(mut db, transaction) => {
                      db.stream_data(py, transaction, query, params, chunk_size)
                          .await
                  }
            }
        })?;

        Ok(result)
    }

    fn commit(&mut self) -> PyResult<()> {
        let _ = futures::executor::block_on(async move {
            match self.transaction.clone() {
                DatabaseTransactionType::Postgres(_, transaction) => {
                    self.commit_internal(transaction).await
                } 
                DatabaseTransactionType::MySql(_, transaction) => {
                      self.commit_internal(transaction).await
                  }
                  DatabaseTransactionType::SQLite(_, transaction) => {
                      self.commit_internal(transaction).await
                  }
            };
        });

        Ok(())
    }

    fn rollback(&self) -> PyResult<()> {
        let _ = futures::executor::block_on(async move {
            match self.transaction.clone() {
                DatabaseTransactionType::Postgres(_, transaction) => {
                    self.rollback_internal(transaction).await
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    self.rollback_internal(transaction).await
                }
                DatabaseTransactionType::SQLite(_, transaction) => {
                    self.rollback_internal(transaction).await
                }
            }
        });

        Ok(())
    }

    fn __del__(&self) {
        let _ = futures::executor::block_on(async move {
            match &self.transaction {
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
                DatabaseTransactionType::SQLite(_, transaction) => {
                    if let Some(transaction) = transaction.lock().await.take() {
                        transaction.rollback().await.ok();
                    }
                }
            }
        });
    }

    fn __exit__(
        &self,
        _exc_type: PyObject,
        _exc_value: PyObject,
        _traceback: PyObject,
    ) -> PyResult<()> {
        let _ = futures::executor::block_on(async move {
            match &self.transaction {
                DatabaseTransactionType::Postgres(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::MySql(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
                DatabaseTransactionType::SQLite(_, transaction) => {
                    transaction.lock().await.take().unwrap().commit().await
                }
            }
        });

        Ok(())
    }
}
