use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use sqlx::{
    mysql::{MySqlConnectOptions, MySqlPoolOptions},
    postgres::{PgConnectOptions, PgPoolOptions},
    sqlite::{SqliteConnectOptions, SqlitePoolOptions},
    Pool,
};
use std::collections::HashMap;
use std::time::Duration;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[pyclass]
pub enum DatabaseType {
    Postgres,
    MySQL,
    SQLite,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[pyclass]
pub struct DatabaseConfig {
    pub driver: DatabaseType,
    pub url: String,

    // Connection pool settings
    #[serde(default = "default_max_connections")]
    pub max_connections: u32,

    #[serde(default = "default_min_connections")]
    pub min_connections: u32,

    #[serde(default = "default_idle_timeout")]
    pub idle_timeout: u64,

    // Additional database-specific options
    pub options: Option<HashMap<String, String>>,
}

// Default configuration values
fn default_max_connections() -> u32 {
    10
}
fn default_min_connections() -> u32 {
    1
}
fn default_idle_timeout() -> u64 {
    600
}

#[pymethods]
impl DatabaseConfig {
    #[new]
    fn new(driver: DatabaseType, url: &str) -> Self {
        DatabaseConfig {
            driver,
            url: url.to_string(),
            max_connections: default_max_connections(),
            min_connections: default_min_connections(),
            idle_timeout: default_idle_timeout(),
            options: None,
        }
    }
}

impl DatabaseConfig {
    // Create PostgreSQL connection pool
    pub async fn create_postgres_pool(&self) -> Result<Pool<sqlx::Postgres>, sqlx::Error> {
        // Parse connection options
        let connect_options = self.url.parse::<PgConnectOptions>()?;

        // Create pool with configured options
        PgPoolOptions::new()
            .max_connections(self.max_connections)
            .min_connections(self.min_connections)
            .idle_timeout(Some(Duration::from_secs(self.idle_timeout)))
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
            DatabaseType::MySQL => {
                let pool = self.create_mysql_pool().await?;
                Ok(Box::new(pool))
            }
            DatabaseType::SQLite => {
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
