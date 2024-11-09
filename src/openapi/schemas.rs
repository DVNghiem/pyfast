use crate::utils::yaml_to_json;
use pyo3::{prelude::*, types::PyDict};
use regex::Regex;
use yaml_rust::YamlLoader;

#[pyclass(subclass)]
pub struct BaseSchemaGenerator{

    #[pyo3(get, set)]
    base_schema: Py<PyDict>,
}

#[pymethods]
impl BaseSchemaGenerator {
    #[new]
    fn new(base_schema: Py<PyDict>) -> Self {
        BaseSchemaGenerator{
            base_schema
        }
    }

    fn remove_converter(&self, path: String) -> String {
        let re = Regex::new(r":\w+}").unwrap();
        re.replace_all(&path, "}").into_owned()
    }

    fn parse_docstring(&self, func_or_method: Py<PyAny>) -> String {
        let docstring: String =
            Python::with_gil(|py| match func_or_method.getattr(py, "__doc__") {
                Ok(doc) => match doc.extract::<String>(py) {
                    Ok(doc) => doc,
                    Err(_) => "".to_string(),
                },
                Err(_) => "".to_string(),
            });
        if docstring.is_empty() {
            return "".to_string();
        }
        let part_of_docs: Vec<&str> = docstring.split("---").collect();
        let part = part_of_docs.last().unwrap();

        match YamlLoader::load_from_str(&part) {
            Ok(docs) => {
                let doc = &docs[0];
                let doc_json = yaml_to_json(doc);
                return doc_json.to_string();
            }
            Err(_e) => {
                return "".to_string();
            }
        }
    }
}
