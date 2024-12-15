use pyo3::prelude::*;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::error;

use crate::database::context::get_sql_connect;

use super::{
    db_trait::DatabaseOperations, mysql::MySqlDatabase, postgresql::PostgresDatabase,
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
    do_commit: bool,
}

impl DatabaseTransaction {
    pub fn from_transaction(transaction: DatabaseTransactionType) -> Self {
        Self {
            transaction,
            do_commit: false,
        }
    }

    async fn renew_transaction<T>(
        &self,
        mut guard: tokio::sync::MutexGuard<'_, Option<sqlx::Transaction<'_, T>>>,
    ) where
        T: sqlx::Database,
    {
        match get_sql_connect() {
            Some(connection) => {
                let transaction = connection.begin_transaction().await;
                let tx = transaction
                    .unwrap()
                    .downcast::<sqlx::Transaction<'static, T>>()
                    .unwrap();
                guard.replace(*tx);
            }
            None => {}
        }
    }

    async fn commit_with_type<T>(
        &mut self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, T>>>>,
    ) where
        T: sqlx::Database,
    {
        let mut guard = transaction.lock().await;
        let transaction = guard.take().unwrap();
        transaction.commit().await.ok();

        self.renew_transaction(guard).await;
    }

    pub async fn commit_internal(&mut self) {
        match self.transaction.clone() {
            DatabaseTransactionType::Postgres(_, transaction) => {
                self.commit_with_type(transaction).await
            }
            DatabaseTransactionType::MySql(_, transaction) => {
                self.commit_with_type(transaction).await
            }
            DatabaseTransactionType::SQLite(_, transaction) => {
                self.commit_with_type(transaction).await
            }
        }
    }

    async fn rollback_with_type<T>(
        &self,
        transaction: Arc<Mutex<Option<sqlx::Transaction<'static, T>>>>,
    ) where
        T: sqlx::Database,
    {
        let mut guard = transaction.lock().await;
        let transaction = guard.take().unwrap();
        transaction.rollback().await.ok();
        self.renew_transaction(guard).await;
    }

    async fn rollback_internal(&mut self) {
        if !self.do_commit {
            return;
        }
        match self.transaction.clone() {
            DatabaseTransactionType::Postgres(_, transaction) => {
                self.rollback_with_type(transaction).await
            }
            DatabaseTransactionType::MySql(_, transaction) => {
                self.rollback_with_type(transaction).await
            }
            DatabaseTransactionType::SQLite(_, transaction) => {
                self.rollback_with_type(transaction).await
            }
        }
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

    fn bulk_change(
        &mut self,
        query: &str,
        params: Vec<Vec<&PyAny>>,
        batch_size: usize,
    ) -> PyResult<u64> {
        let transaction = self.transaction.clone();
        let result = futures::executor::block_on(async move {
            let row_effect = match transaction {
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.bulk_change(transaction, query, params, batch_size).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.bulk_change(transaction, query, params, batch_size).await
                }
                DatabaseTransactionType::SQLite(mut db, transaction) => {
                    db.bulk_change(transaction, query, params, batch_size).await
                }
            };
            Ok(match row_effect {
                Ok(row) => {
                    self.do_commit = true;
                    row
                }
                Err(e) => {
                    self.rollback_internal().await;
                    error!("Error in bulk_change: {:?}", e);
                    return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        e.to_string(),
                    ));
                }
            })
        })?;

        Ok(result)
    }

    fn commit(&mut self) -> PyResult<()> {
        let _ = futures::executor::block_on(async move {
            self.commit_internal().await;
        });
        Ok(())
    }

    fn rollback(&mut self) -> PyResult<()> {
        let _ = futures::executor::block_on(async move {
            self.rollback_internal().await;
        });
        Ok(())
    }
}
