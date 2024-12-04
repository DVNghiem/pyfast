# Getting Started with Hypern

## Installation

```bash
pip install hypern
```

## Basic Application Setup

Here's a basic example of creating a Hypern application:

```python
from hypern import Hypern
from hypern.routing import Route, HTTPEndpoint
from hypern.response import PlainTextResponse

# Create a basic endpoint
class DefaultRoute(HTTPEndpoint):
    async def get(self):
        return PlainTextResponse("Hello, World!")

# Create routes list
routes = [
    Route("/hello", DefaultRoute),
]

# Initialize the application
app = Hypern(
    routes=routes,
    title="My API",
    version="1.0.0",
    description="My first Hypern API"
)

# Start the server
if __name__ == "__main__":
    app.start()
```

## Route Decorators

You can also use decorators to define routes:

```python
from hypern.routing import Route

route = Route("/api")

@route.get("/hello")
def hello():
    return PlainTextResponse("Hello from decorator!")
```

## WebSocket Support

Adding WebSocket endpoints:

```python
from hypern.ws import WebsocketRoute, WebSocketSession

ws = WebsocketRoute()

@ws.on("/ws")
def handle_websocket(session: WebSocketSession, message: str):
    session.send("Received: " + message)
    return "Connection established"

# Add WebSocket routes to app
app.add_websocket(ws)
```

## Request Validation

Using Pydantic models for request validation:

```python
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int

class UserRoute(HTTPEndpoint):
    async def post(self, form_data: UserModel):
        return PlainTextResponse(f"Created user: {form_data.name}")
```

## Running the Application

The application can be started with various configuration options:

```bash
# Basic start
python app.py

# With custom host and port
python app.py --host 0.0.0.0 --port 8000

# With hot reload for development
python app.py --reload

# With multiple workers
python app.py --workers 4
```

## Command Line Arguments

Hypern supports various command-line arguments for server configuration:

```bash
# Available arguments:
--host              # Server host address [default: 127.0.0.1]
--port              # Server port [default: 5000]
--processes         # Number of processes [default: 1]
--workers           # Number of workers per process [default: 1]
--max-blocking-threads  # Maximum blocking threads [default: 100]
--reload           # Enable hot reload [flag]

# Examples:
python app.py --host 0.0.0.0 --port 8080
python app.py --workers 4 --processes 2
python app.py --max-blocking-threads 200
```

The arguments can be combined as needed for your specific deployment requirements.

## API Documentation

By default, Hypern provides automatic API documentation at:
- Swagger UI: `http://localhost:5000/docs`
- OpenAPI JSON: `http://localhost:5000/openapi.json`

## Middleware Support

Adding middleware to your application:

```python
from hypern.middleware import CORSMiddleware

app = Hypern(routes=routes)
app.add_middleware(CORSMiddleware())
```

For more detailed information and advanced features, visit the official documentation.
