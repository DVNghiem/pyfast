# Getting Started with Hypern

## Installation

```bash
pip install hypern
```

## Creating a Basic Application

Here's a simple example of creating a Hypern application:

```python
from hypern import Hypern, Request
from hypern.routing import HTTPEndpoint, Route
from hypern.response import JSONResponse

# Create an endpoint
class HelloWorld(HTTPEndpoint):
    async def get(self, request: Request):
        return JSONResponse({"message": "Hello, World!"})

# Define routes
routes = [
    Route("/hello", HelloWorld)
]

# Create application
app = Hypern(
    routes=routes,
    title="My API",
    description="A sample Hypern application",
    version="1.0.0"
)

if __name__ == "__main__":
    app.start()
```

## Command Line Arguments

Hypern supports several command-line arguments for configuration:

```bash
# Basic usage
python app.py --host 0.0.0.0 --port 8000

# Available arguments:
--host                  # Server host (default: 127.0.0.1)
--port                  # Server port (default: 5000)
--processes            # Number of processes (default: 1)
--workers              # Number of workers (default: 1)
--max-blocking-threads # Maximum blocking threads (default: 100)
--reload               # Enable auto-reload on file changes
```

## Example with All Configuration Options

```python
from hypern import Hypern
from hypern.datastructures import Contact, License

app = Hypern(
    routes=routes,
    title="My API",
    summary="API Summary",
    description="Detailed API description",
    version="1.0.0",
    contact=Contact(
        name="API Support",
        email="support@example.com",
        url="https://example.com/support"
    ),
    license_info=License(
        name="MIT",
        url="https://opensource.org/licenses/MIT"
    ),
    openapi_url="/openapi.json",  # OpenAPI schema URL
    docs_url="/docs"              # Swagger UI URL
)

if __name__ == "__main__":
    app.start()
```

Once started, you can access:
- Your API at `http://localhost:5000`
- API documentation at `http://localhost:5000/docs`
- OpenAPI schema at `http://localhost:5000/openapi.json`