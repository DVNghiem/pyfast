use dashmap::DashMap;
use lazy_static::lazy_static;
use once_cell::sync::OnceCell;
use pyo3::prelude::*;

use super::sql::{connection::DatabaseConnection, transaction::DatabaseTransaction};

lazy_static! {
    static ref SQL_SESSION_MAPPING: DashMap<String, DatabaseTransaction> = DashMap::new();
}

pub fn get_sql_session_mapping() -> &'static DashMap<String, DatabaseTransaction> {
    &SQL_SESSION_MAPPING
}

pub fn insert_sql_session(session_id: &str, database: DatabaseTransaction) {
    SQL_SESSION_MAPPING.insert(session_id.to_string(), database);
}

pub fn remove_sql_session(session_id: &str) {
    SQL_SESSION_MAPPING.remove(session_id);
}

#[pyfunction]
pub fn get_session_database(session_id: &str) -> Option<DatabaseTransaction> {
    let mapping = get_sql_session_mapping();
    mapping.get(session_id).map(|x| x.value().clone())
}

static SQL_DATABASE_CONNECTION: OnceCell<DatabaseConnection> = OnceCell::new();

pub fn get_sql_connect() -> Option<&'static DatabaseConnection> {
    SQL_DATABASE_CONNECTION.get()
}

pub fn set_sql_connect(connection: DatabaseConnection) {
    let _ = SQL_DATABASE_CONNECTION.set(connection);
}
