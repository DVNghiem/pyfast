use pyo3::{types::{PyBytes, PyString}, PyAny, PyResult};
use yaml_rust::Yaml;
use serde_json::Value;
use tokio::runtime::Runtime;

use once_cell::sync::OnceCell;

static RUNTIME: OnceCell<Runtime> = OnceCell::new();

pub fn get_runtime() -> &'static Runtime {
    RUNTIME.get_or_init(|| Runtime::new().unwrap())
}

pub fn yaml_to_json(yaml: &Yaml) -> Value {
    match yaml {
        Yaml::Real(s) | Yaml::String(s) => Value::String(s.clone()),
        Yaml::Integer(i) => Value::Number((*i).into()),
        Yaml::Boolean(b) => Value::Bool(*b),
        Yaml::Array(a) => Value::Array(a.iter().map(yaml_to_json).collect()),
        Yaml::Hash(h) => {
            let mut map = serde_json::Map::new();
            for (k, v) in h {
                if let Yaml::String(key) = k {
                    map.insert(key.clone(), yaml_to_json(v));
                }
            }
            Value::Object(map)
        }
        Yaml::Null => Value::Null,
        Yaml::BadValue => Value::Null,
        _ => Value::Null,
    }
}

pub fn get_description_from_pyobject(description: &PyAny) -> PyResult<Vec<u8>> {
    if let Ok(s) = description.downcast::<PyString>() {
        Ok(s.to_string().into_bytes())
    } else if let Ok(b) = description.downcast::<PyBytes>() {
        Ok(b.as_bytes().to_vec())
    } else {
        Ok(vec![])
    }
}