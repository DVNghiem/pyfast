use yaml_rust::Yaml;
use serde_json::Value;

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