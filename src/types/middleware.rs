use super::{request, response};


#[allow(clippy::large_enum_variant)]
#[derive(Debug)]
pub enum MiddlewareReturn {
    Request(request::Request),
    Response(response::Response),
}