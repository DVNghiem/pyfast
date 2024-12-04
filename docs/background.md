# Background Tasks in Hypern

Background tasks in Hypern allow you to execute operations asynchronously after the response has been sent to the client. This is useful for operations like:
- Sending emails
- Processing files
- Running long-running computations
- Cleanup operations

## Basic Usage

```python
from hypern.background import BackgroundTask
from hypern.response import PlainTextResponse

def send_email(to: str, subject: str):
    # Email sending logic here
    print(f"Sending email to {to} with subject: {subject}")

@app.route("/send-notification")
async def send_notification():
    background = BackgroundTask(
        send_email,
        args=["user@example.com", "Welcome!"],
        kwargs={}
    )
    return PlainTextResponse(
        "Notification scheduled",
        backgrounds=[background]
    )
```

## Multiple Background Tasks

You can add multiple background tasks that will be executed in order:

```python 
from hypern.background import BackgroundTask, BackgroundTasks

def task1():
    print("Executing task 1")

def task2():
    print("Executing task 2")

@app.route("/multiple-tasks")
async def multiple_tasks():
    tasks = [
        BackgroundTask(task1, [], {}),
        BackgroundTask(task2, [], {})
    ]
    return PlainTextResponse(
        "Tasks scheduled",
        backgrounds=tasks
    )
```

## Task Parameters

The `BackgroundTask` constructor accepts:

- `func`: The function to execute
- `args`: List of positional arguments
- `kwargs`: Dictionary of keyword arguments

## Important Notes

1. Background tasks run after the response is sent
2. Tasks are executed in the order they are added
3. If a task fails, subsequent tasks will still execute
4. Tasks should be relatively quick to avoid blocking the server
5. For long-running tasks, consider using a proper task queue system

## Example with File Response

```python
from hypern.response import FileResponse
from hypern.background import BackgroundTask

def cleanup_temp_file(filepath: str):
    import os
    os.remove(filepath)

@app.route("/download")
async def download():
    return FileResponse(
        content=b"file content",
        filename="report.pdf",
        backgrounds=[
            BackgroundTask(
                cleanup_temp_file,
                args=["temp_file.pdf"],
                kwargs={}
            )
        ]
    )
```