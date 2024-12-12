use std::sync::Arc;

use sqlx::{Error as SqlxError, Pool};
use tokio::sync::Mutex;

use super::{
    config::DatabaseConfig,
    mysql::MySqlDatabase,
    postgresql::PostgresDatabase,
    sqlite::SqliteDatabase,
    transaction::{DatabaseTransaction, DatabaseTransactionType},
};

#[derive(Clone)]
enum DatabaseType {
    Postgres(Arc<Pool<sqlx::Postgres>>),
    MySql(Arc<Pool<sqlx::MySql>>),
    SQLite(Arc<Pool<sqlx::Sqlite>>),
}

#[derive(Clone)]
pub struct DatabaseConnection {
    connection: DatabaseType,
}

impl DatabaseConnection {
    pub async fn new(config: DatabaseConfig) -> Self {
        let connection = match config.driver {
            super::config::DatabaseType::Postgres => {
                let pool = config.create_postgres_pool().await.unwrap();
                Ok::<DatabaseType, SqlxError>(DatabaseType::Postgres(Arc::new(pool)))
            }
            super::config::DatabaseType::MySQL => {
                let pool = config.create_mysql_pool().await.unwrap();
                Ok::<DatabaseType, SqlxError>(DatabaseType::MySql(Arc::new(pool)))
            }
            super::config::DatabaseType::SQLite => {
                let pool = config.create_sqlite_pool().await.unwrap();
                Ok::<DatabaseType, SqlxError>(DatabaseType::SQLite(Arc::new(pool)))
            }
        }
        .unwrap();

        Self { connection }
    }

    // get transaction
    pub async fn transaction(&self) -> DatabaseTransaction {
        match &self.connection {
            DatabaseType::Postgres(pool) => {
                let transaction = pool
                    .begin()
                    .await
                    .map_err(|e| SqlxError::Configuration(e.to_string().into()));
                DatabaseTransaction::from_transaction(DatabaseTransactionType::Postgres(
                    PostgresDatabase,
                    Arc::new(Mutex::new(Some(transaction.unwrap()))),
                ))
            }
            DatabaseType::MySql(pool) => {
                let transaction = pool
                    .begin()
                    .await
                    .map_err(|e| SqlxError::Configuration(e.to_string().into()));
                DatabaseTransaction::from_transaction(DatabaseTransactionType::MySql(
                    MySqlDatabase,
                    Arc::new(Mutex::new(Some(transaction.unwrap()))),
                ))
            }
            DatabaseType::SQLite(pool) => {
                let transaction = pool
                    .begin()
                    .await
                    .map_err(|e| SqlxError::Configuration(e.to_string().into()));
                DatabaseTransaction::from_transaction(DatabaseTransactionType::SQLite(
                    SqliteDatabase,
                    Arc::new(Mutex::new(Some(transaction.unwrap()))),
                ))
            }
        }
    }
}
