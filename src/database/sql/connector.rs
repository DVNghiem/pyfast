use pyo3::prelude::*;
use sqlx::Error as SqlxError;
use tokio::runtime::Runtime;

use super::{
    config::DatabaseConfig, db_trait::DatabaseOperations, mysql::MySqlDatabase,
    postgresql::PostgresDatabase, sqlite::SqliteDatabase,
};

#[derive(Clone)]
enum DatabaseType {
    Sqlite(SqliteDatabase, <SqliteDatabase as DatabaseOperations>::Pool),
    Postgres(
        PostgresDatabase,
        <PostgresDatabase as DatabaseOperations>::Pool,
    ),
    MySql(MySqlDatabase, <MySqlDatabase as DatabaseOperations>::Pool),
    // Mssql(MssqlDb, <MssqlDb as DatabaseOperations>::Pool),
}

#[pyclass]
pub struct DatabaseConnection {
    runtime: Runtime,
    connection: DatabaseType,
}

#[pymethods]
impl DatabaseConnection {
    #[new]
    fn new(config: DatabaseConfig) -> PyResult<Self> {
        let runtime = Runtime::new()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let connection = runtime
            .block_on(async move {
                match config.driver {
                    super::config::DatabaseType::SQLite => {
                        let pool = config
                            .create_sqlite_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::Sqlite(SqliteDatabase, pool))
                    }
                    super::config::DatabaseType::Postgres => {
                        let pool = config
                            .create_postgres_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::Postgres(
                            PostgresDatabase,
                            pool,
                        ))
                    }
                    super::config::DatabaseType::MySQL => {
                        let pool = config
                            .create_mysql_pool()
                            .await
                            .map_err(|e| SqlxError::Configuration(e.to_string().into()))?;
                        Ok::<DatabaseType, SqlxError>(DatabaseType::MySql(MySqlDatabase, pool))
                    } // Add other database types
                }
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(Self {
            runtime,
            connection,
        })
    }

    fn execute(&self, query: &str, params: Vec<&PyAny>) -> PyResult<u64> {
        let result = self.runtime.block_on(async move {
            match &self.connection {
                DatabaseType::Sqlite(db, pool) => db.execute(pool, query, params).await,
                DatabaseType::Postgres(db, pool) => db.execute(pool, query, params).await,
                DatabaseType::MySql(db, pool) => db.execute(pool, query, params).await,
                // Add other database types
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
        let result = self.runtime.block_on(async move {
            match &self.connection {
                DatabaseType::Sqlite(db, pool) => db.fetch_all(py, pool, query, params).await,
                DatabaseType::Postgres(db, pool) => db.fetch_all(py, pool, query, params).await,
                DatabaseType::MySql(db, pool) => db.fetch_all(py, pool, query, params).await,
                // Add other database types
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
        let result = self.runtime.block_on(async move {
            match &self.connection {
                DatabaseType::Sqlite(db, pool) => {
                    db.stream_data(py, pool, query, params, chunk_size).await
                }
                DatabaseType::Postgres(db, pool) => {
                    db.stream_data(py, pool, query, params, chunk_size).await
                }
                DatabaseType::MySql(db, pool) => {
                    db.stream_data(py, pool, query, params, chunk_size).await
                } // Add other database types
            }
        })?;

        Ok(result)
    }
}
