use pyo3::prelude::*;
use std::sync::Arc;
use tokio::sync::Mutex;

use super::{
    db_trait::DatabaseOperations, mysql::MySqlDatabase, postgresql::PostgresDatabase,
    sqlite::SqliteDatabase,
};

#[derive(Debug, Clone)]
pub enum DatabaseTransactionType {
    Postgres(
        PostgresDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::Postgres>>>,
    ),
    MySql(
        MySqlDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::MySql>>>,
    ),
    SQLite(
        SqliteDatabase,
        Arc<Mutex<sqlx::Transaction<'static, sqlx::Sqlite>>>,
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
}

#[pymethods]
impl DatabaseTransaction {
    // fn execute(&self, query: &str, params: Vec<&PyAny>) -> PyResult<u64> {
    //     let transaction = self.transaction.clone();
    //     let result = get_db_runtime().block_on(async move {
    //         match transaction {
    //             DatabaseTransactionType::Postgres(mut db, transaction) => {
    //                 db.execute(transaction, query, params).await
    //             }
    //             // DatabaseTransactionType::MySql(mut db, transaction) => {
    //             //     db.execute(transaction, query, params).await
    //             // } // Add other database types
    //             // DatabaseTransactionType::Sqlite(mut db, transaction) => {
    //             //     db.execute(transaction, query, params).await
    //             // }
    //         }
    //     })?;

    //     Ok(result)
    // }

    fn fetch_all(
        &self,
        py: Python<'_>,
        query: &str,
        params: Vec<&PyAny>,
    ) -> Result<Vec<PyObject>, PyErr> {
        let transaction = self.transaction.clone();
        let result = futures::executor::block_on(async move {
            match transaction {
                DatabaseTransactionType::Postgres(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
                DatabaseTransactionType::MySql(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                } // Add other database types
                DatabaseTransactionType::SQLite(mut db, transaction) => {
                    db.fetch_all(py, transaction, query, params).await
                }
            }
        })?;

        Ok(result)
    }

    // fn stream_data(
    //     &self,
    //     py: Python<'_>,
    //     query: &str,
    //     params: Vec<&PyAny>,
    //     chunk_size: usize,
    // ) -> PyResult<Vec<Vec<PyObject>>> {
    //     let result = get_db_runtime().block_on(async move {
    //         let transaction = self.transaction.clone();
    //         match transaction {
    //             DatabaseTransactionType::Postgres(mut db, transaction) => {
    //                 db.stream_data(py, transaction, query, params, chunk_size)
    //                     .await
    //             }
    //             // DatabaseTransactionType::MySql(mut db, transaction) => {
    //             //     db.stream_data(py, transaction, query, params, chunk_size)
    //             //         .await
    //             // } // Add other database types
    //             // DatabaseTransactionType::Sqlite(mut db, transaction) => {
    //             //     db.stream_data(py, transaction, query, params, chunk_size)
    //             //         .await
    //             // }
    //         }
    //     })?;

    //     Ok(result)
    // }

    // fn commit(&self) -> PyResult<()> {
    //     let result = get_db_runtime().block_on(async move {
    //         match &self.transaction {
    //             DatabaseTransactionType::Postgres(_, transaction) => {
    //                 match transaction.lock().await.take() {
    //                     Some(transaction) => transaction.commit().await,
    //                     None => Ok(()),
    //                 }
    //             }
    //             // DatabaseTransactionType::MySql(_, transaction) => {
    //             //     match transaction.lock().await.take() {
    //             //         Some(transaction) => transaction.commit().await,
    //             //         None => Ok(()),
    //             //     }
    //             // }
    //             // DatabaseTransactionType::Sqlite(_, transaction) => {
    //             //     match transaction.lock().await.take() {
    //             //         Some(transaction) => transaction.commit().await,
    //             //         None => Ok(()),
    //             //     }
    //             // }
    //         }
    //     });

    //     result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
    //     Ok(())
    // }

    // fn rollback(&self) -> PyResult<()> {
    //     let result = get_db_runtime().block_on(async move {
    //         match &self.transaction {
    //             DatabaseTransactionType::Postgres(_, transaction) => {
    //                 match transaction.lock().await.take() {
    //                     Some(transaction) => transaction.rollback().await,
    //                     None => Ok(()),
    //                 }
    //             }
    //             // DatabaseTransactionType::MySql(_, transaction) => {
    //             //     match transaction.lock().await.take() {
    //             //         Some(transaction) => transaction.rollback().await,
    //             //         None => Ok(()),
    //             //     }
    //             // }
    //             // DatabaseTransactionType::Sqlite(_, transaction) => {
    //             //     match transaction.lock().await.take() {
    //             //         Some(transaction) => transaction.rollback().await,
    //             //         None => Ok(()),
    //             //     }
    //             // }
    //         }
    //     });

    //     result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
    //     Ok(())
    // }

    // fn __del__(&self) {
    //     let _ = get_db_runtime().block_on(async move {
    //         match &self.transaction {
    //             DatabaseTransactionType::Postgres(_, transaction) => {
    //                 if let Some(transaction) = transaction.lock().await.take() {
    //                     transaction.rollback().await.ok();
    //                 }
    //             }
    //             // DatabaseTransactionType::MySql(_, transaction) => {
    //             //     if let Some(transaction) = transaction.lock().await.take() {
    //             //         transaction.rollback().await.ok();
    //             //     }
    //             // }
    //             // DatabaseTransactionType::Sqlite(_, transaction) => {
    //             //     if let Some(transaction) = transaction.lock().await.take() {
    //             //         transaction.rollback().await.ok();
    //             //     }
    //             // }
    //         }
    //     });
    // }

    // fn __enter__(&self) -> PyResult<()> {
    //     Ok(())
    // }

    // fn __exit__(&self, _exc_type: PyObject, _exc_value: PyObject, _traceback: PyObject) -> PyResult<()> {
    //     let result = get_db_runtime().block_on(async move {
    //         match &self.transaction {
    //             DatabaseTransactionType::Postgres(_, transaction) => {
    //                 transaction.lock().await.take().unwrap().commit().await
    //             }
    //             // DatabaseTransactionType::MySql(_, transaction) => {
    //             //     transaction.lock().await.take().unwrap().commit().await
    //             // }
    //             // DatabaseTransactionType::Sqlite(_, transaction) => {
    //             //     transaction.lock().await.take().unwrap().commit().await
    //             // }
    //         }
    //     });

    //     result.map_err(|e| PyErr::new::<PyException, _>(e.to_string()))?;
    //     Ok(())
    // }
}
