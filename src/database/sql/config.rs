use pyo3::prelude::*;
use sqlx::{
    mysql::{MySqlConnectOptions, MySqlPoolOptions},
    postgres::{PgConnectOptions, PgPoolOptions},
    sqlite::{SqliteConnectOptions, SqlitePoolOptions},
    ConnectOptions, Pool,
};
use std::collections::HashMap;
use std::time::Duration;
use tracing::log::LevelFilter;

#[derive(Debug, Clone)]
#[pyclass]
pub enum DatabaseType {
    Postgres,
    Mysql,
    Sqlite,
}

impl Default for DatabaseType {
    fn default() -> Self {
        DatabaseType::Postgres
    }
}

#[derive(Debug, Clone, Default)]
#[pyclass]
pub struct DatabaseConfig {
    pub driver: DatabaseType,
    pub url: String,

    // Connection pool settings
    pub max_connections: u32,

    pub min_connections: u32,

    pub idle_timeout: u64,

    // Additional database-specific options
    pub options: Option<HashMap<String, String>>,
}

#[pymethods]
impl DatabaseConfig {
    #[new]
    fn new(
        driver: DatabaseType,
        url: &str,
        max_connections: u32,
        min_connections: u32,
        idle_timeout: u64,
        options: Option<HashMap<String, String>>,
    ) -> Self {
        DatabaseConfig {
            driver,
            url: url.to_string(),
            max_connections,
            min_connections,
            idle_timeout,
            options,
        }
    }
}

impl DatabaseConfig {
    // Create PostgreSQL connection pool
    pub async fn create_postgres_pool(&self) -> Result<Pool<sqlx::Postgres>, sqlx::Error> {
        // Parse connection options

        let mut connect_options = self.url.parse::<PgConnectOptions>()?;
        connect_options = connect_options.log_statements(LevelFilter::Debug);

        // Create pool with configured options
        PgPoolOptions::new()
            .max_connections(self.max_connections)
            .min_connections(self.min_connections)
            .idle_timeout(Some(Duration::from_secs(self.idle_timeout)))
            .acquire_timeout(Duration::from_secs(self.idle_timeout))
            .connect_with(connect_options)
            .await
    }

    // Create MySQL connection pool
    pub async fn create_mysql_pool(&self) -> Result<Pool<sqlx::MySql>, sqlx::Error> {
        let connect_options = self.url.parse::<MySqlConnectOptions>()?;

        MySqlPoolOptions::new()
            .max_connections(self.max_connections)
            .min_connections(self.min_connections)
            .idle_timeout(Some(Duration::from_secs(self.idle_timeout)))
            .acquire_timeout(Duration::from_secs(self.idle_timeout))
            .connect_with(connect_options)
            .await
    }

    // Create SQLite connection pool
    pub async fn create_sqlite_pool(&self) -> Result<Pool<sqlx::Sqlite>, sqlx::Error> {
        let connect_options = self.url.parse::<SqliteConnectOptions>()?;

        SqlitePoolOptions::new()
            .max_connections(self.max_connections)
            .min_connections(self.min_connections)
            .idle_timeout(Some(Duration::from_secs(self.idle_timeout)))
            .connect_with(connect_options)
            .await
    }

    // Dynamic pool creation based on database type
    pub async fn create_pool(&self) -> Result<Box<dyn DatabasePoolTrait>, sqlx::Error> {
        match self.driver {
            DatabaseType::Postgres => {
                let pool = self.create_postgres_pool().await?;
                Ok(Box::new(pool))
            }
            DatabaseType::Mysql => {
                let pool = self.create_mysql_pool().await?;
                Ok(Box::new(pool))
            }
            DatabaseType::Sqlite => {
                let pool = self.create_sqlite_pool().await?;
                Ok(Box::new(pool))
            }
        }
    }

    // Generate default configuration
    pub fn default_postgres(url: &str) -> Self {
        DatabaseConfig {
            driver: DatabaseType::Postgres,
            url: url.to_string(),
            max_connections: 10,
            min_connections: 1,
            idle_timeout: 600,
            options: None,
        }
    }
}

// Trait for dynamic pool handling
pub trait DatabasePoolTrait: Send + Sync {}

impl DatabasePoolTrait for Pool<sqlx::Postgres> {}
impl DatabasePoolTrait for Pool<sqlx::MySql> {}
impl DatabasePoolTrait for Pool<sqlx::Sqlite> {}
