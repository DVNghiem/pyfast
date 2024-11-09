use pyo3::prelude::*;
use pyo3::types::*;

#[pyclass]
pub struct SwaggerUI {
    #[pyo3(get, set)]
    title: String,

    #[pyo3(get, set)]
    openapi_url: String,
}

#[pymethods]
impl SwaggerUI {
    #[new]
    fn new(title: String, openapi_url: String) -> Self {
        SwaggerUI {
            title,
            openapi_url,
        }
    }

    fn render_template(&self) -> PyObject {
        Python::with_gil(|py| {
            let robyn_module = py.import("robyn").unwrap();
            let response = robyn_module.getattr("Response").unwrap();
            let status_code = 200;
            let description = self.get_html_contant();
            let headers = PyDict::new(py);
            headers.set_item("Content-type", "text/html").unwrap();
            response.call1((status_code, headers, description)).unwrap().to_object(py)
        })
    }

    fn get_html_contant(&self) -> String{
        let oauth2_redirect_url = false;// TODO

        let mut html = format!(
            r#"
                <!DOCTYPE html>
                 <html>
                 <head>
                 <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
                 <link rel="shortcut icon" href="https://res.cloudinary.com/dslpmba3s/image/upload/v1731161593/logo/pyfast-180x180.png">
                 <title>{}</title>
                 </head>
                 <body>
                 <div id="swagger-ui">
                 </div>
                 <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
                 <!-- `SwaggerUIBundle` is now available on the page -->
                 <script>
                 const ui = SwaggerUIBundle({{
                     url: '{}',
            "#,
            self.title, self.openapi_url
        );
        if oauth2_redirect_url {
            html.push_str(
                format!(r#"
                    oauth2RedirectUrl: window.location.origin + '{}',
                "#,
                oauth2_redirect_url
                ).as_str(),
            );
        }
        html.push_str(
            r#"
                dom_id: '#swagger-ui',
                presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            });
            </script>
            </body>
            </html>
            "#,
        );
        html
    }
}
