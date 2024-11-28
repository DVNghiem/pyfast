use pyo3::prelude::*;
use sqlx::{Error as SqlxError, Pool};

use crate::utils::get_db_runtime;

use super::{
    config::DatabaseConfig,
    mysql::MySqlDatabase,
    postgresql::PostgresDatabase,
    sqlite::SqliteDatabase,
    transaction::{DatabaseTransaction, DatabaseTransactionType},
};

#[derive(Clone)]
enum DatabaseType {
    Sqlite(Pool<sqlx::Sqlite>),
    Postgres(Pool<sqlx::Postgres>),
    MySql(Pool<sqlx::MySql>),
}

#[pyclass]
pub struct DatabaseConnection {
    connection: DatabaseType,
}

#[pymethods]
impl DatabaseConnection {
    #[new]
    fn new(config: DatabaseConfig) -> PyResult<Self> {
        let connection = get_db_runtime()
            .block_on(async move {
                match config.driver {
                    super::config::DatabaseType::SQLite => {
                        let pool = config
                            .create_sqlite_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::Sqlite(pool))
                    }
                    super::config::DatabaseType::Postgres => {
                        let pool = config
                            .create_postgres_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::Postgres(pool))
                    }
                    super::config::DatabaseType::MySQL => {
                        let pool = config
                            .create_mysql_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::MySql(pool))
                    } // Add other database types
                }
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(Self { connection })
    }

    // get transaction
    fn transaction(&self) -> PyResult<DatabaseTransaction> {
        let transaction = get_db_runtime()
            .block_on(async move {
                match &self.connection {
                    DatabaseType::Sqlite(pool) => {
                        let transaction = pool
                            .begin()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseTransaction, SqlxError>(DatabaseTransaction::from_transaction(
                            DatabaseTransactionType::Sqlite(
                                SqliteDatabase,
                                std::sync::Arc::new(tokio::sync::Mutex::new(Some(transaction))),
                            ),
                        ))
                    }
                    DatabaseType::Postgres(pool) => {
                        let transaction = pool
                            .begin()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseTransaction, SqlxError>(DatabaseTransaction::from_transaction(
                            DatabaseTransactionType::Postgres(
                                PostgresDatabase,
                                std::sync::Arc::new(tokio::sync::Mutex::new(Some(transaction))),
                            ),
                        ))
                    }
                    DatabaseType::MySql(pool) => {
                        let transaction = pool
                            .begin()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseTransaction, SqlxError>(DatabaseTransaction::from_transaction(
                            DatabaseTransactionType::MySql(
                                MySqlDatabase,
                                std::sync::Arc::new(tokio::sync::Mutex::new(Some(transaction))),
                            ),
                        ))
                    }
                }
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(transaction)
    }
}
