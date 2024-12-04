# Response Types in Hypern

This document outlines the different response types available in the Hypern framework and their specific use cases.

## Base Response Class

The `BaseResponse` class is the foundation for all response types. It handles:
- Status code management
- Headers initialization
- Content rendering
- Background task handling

## Available Response Types

### Response
```python
from hypern.responses import Response

# Basic response with default settings
response = Response(content="Hello World")
```
Used for general-purpose responses where no specific media type is required.

### JSONResponse
```python
from hypern.responses import JSONResponse

# JSON response with data
response = JSONResponse(
    content={"message": "Success", "data": [1, 2, 3]},
    status_code=200
)
```
Automatically sets `content-type: application/json` and serializes Python objects to JSON.

### HTMLResponse
```python
from hypern.responses import HTMLResponse

# HTML response
response = HTMLResponse(
    content="<html><body><h1>Hello World</h1></body></html>"
)
```
Used for returning HTML content with `content-type: text/html`.

### PlainTextResponse
```python
from hypern.responses import PlainTextResponse

# Plain text response
response = PlainTextResponse(content="Hello World")
```
Returns plain text with `content-type: text/plain`.

### RedirectResponse
```python
from hypern.responses import RedirectResponse

# Redirect to another URL
response = RedirectResponse(
    url="/new-location",
    status_code=307  # Temporary redirect
)
```
Handles URL redirections with appropriate status codes.

### FileResponse
```python
from hypern.responses import FileResponse

# File download response
response = FileResponse(
    content=file_bytes,
    filename="document.pdf"
)
```
Configures response for file downloads with proper headers.

## Common Parameters

All response types accept these common parameters:
- `status_code`: HTTP status code (default: 200)
- `headers`: Optional dictionary of custom headers
- `backgrounds`: List of background tasks to execute

## Background Tasks

Responses can include background tasks that execute after the response is sent:
```python
from hypern.background import BackgroundTask

async def notify():
    # Notification logic here
    pass

response = JSONResponse(
    content={"status": "success"},
    backgrounds=[BackgroundTask(notify)]
)
```