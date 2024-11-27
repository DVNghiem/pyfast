# Background Tasks in Hypern

Background tasks allow you to execute operations asynchronously after returning a response. This is useful for operations like:

- Sending emails
- Processing uploaded files
- Executing long-running tasks
- Cleanup operations

## Basic Usage

```python
from hypern.background import BackgroundTask
from hypern.responses import JSONResponse

def send_email(email: str, message: str):
    # Email sending logic here
    pass

async def create_user(request):
    # Create user logic
    
    background = BackgroundTask(
        id="send_welcome_email",
        function=send_email,
        args=["user@example.com", "Welcome!"],
        kwargs={},
        timeout_secs=30,
        cancelled=False
    )

    return JSONResponse(
        content={"message": "User created"},
        backgrounds=[background]
    )
```

## Managing Multiple Tasks

```python
from hypern.background import BackgroundTasks

background_tasks = BackgroundTasks()

# Add multiple tasks
task1 = BackgroundTask(...)
task2 = BackgroundTask(...)

background_tasks.add_task(task1) 
background_tasks.add_task(task2)

# Execute specific task
background_tasks.execute_task(task1.get_id())

# Execute all tasks
background_tasks.execute_all()

# Cancel a task
background_tasks.cancel_task(task1.get_id())
```

## Task Configuration

- `id`: Unique identifier for the task
- `function`: The function to execute
- `args`: List/Tuple of positional arguments
- `kwargs`: Dictionary of keyword arguments  
- `timeout_secs`: Maximum execution time
- `cancelled`: Flag to cancel task

## Notes

- Tasks run synchronously for now
- Tasks are executed after the response is sent
- Tasks should be idempotent in case of retries
- Use timeouts to prevent hanging tasks