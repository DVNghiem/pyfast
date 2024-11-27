# Hypern Scheduler

The Scheduler component in Hypern provides functionality for scheduling and managing background jobs.

## Basic Usage

## Basic Usage

```python
from hypern import Hypern, Scheduler
from hypern.routing import Route, HTTPEndpoint
from hypern.response import JSONResponse

# Define example task
async def my_task():
    print("Running scheduled task")

scheduler = Scheduler()

# Define scheduler endpoint
class SchedulerEndpoint(HTTPEndpoint):
    async def post(self, request):
        job_id = app.scheduler.add_job(
            job_type="cron", 
            schedule_param="*/5 * * * *",  # Run every 5 minutes
            task=my_task,
            timezone="UTC"
        )
        return JSONResponse({"job_id": job_id})
    
    async def get(self, request):
        jobs = app.scheduler.get_jobs()
        return JSONResponse({"jobs": jobs})
        
routing = [
    Route("/test", SchedulerEndpoint),
]
app = Hypern(
    routes=routing,
    scheduler=scheduler,
)

```

## Job Types

The scheduler supports two types of jobs:

- **Cron Jobs**: Run on a schedule using cron expressions
- **Interval Jobs**: Run at fixed time intervals

### Cron Jobs

Cron jobs use standard cron expressions in the format:

```
* * * * * * *
| | | | | | |
| | | | | | +-- Year              (range: 1900-3000)
| | | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
| | | | +------ Month of the Year (range: 1-12)
| | | +-------- Day of the Month  (range: 1-31)
| | +---------- Hour              (range: 0-23)
| +------------ Minute            (range: 0-59)
+-------------- Second            (range: 0-59)
```

Example:

```python
# Run at 9:30 AM every Monday 
scheduler.add_job(
    job_type="cron",
    schedule_param="0 30 9 * * 1",
    task=my_task,
    timezone="UTC"
)
```

### Interval Jobs

Interval jobs run at fixed time intervals specified in seconds.

Example:

```python 
# Run every 5 minutes
scheduler.add_job(
    job_type="interval",
    schedule_param="300", # 5 minutes in seconds
    task=my_task,
    timezone="UTC"
)
```

## Job Management

### Adding Jobs

```python
job_id = scheduler.add_job(
    job_type="cron",
    schedule_param="*/5 * * * *",
    task=my_task,
    timezone="UTC",
    dependencies=["job1", "job2"],
    retry_policy=(3, 60, True) # Max retries, delay, exponential backoff
)
```

Parameters:

- `job_type`: "cron" or "interval" 
- `schedule_param`: Cron expression or interval in seconds
- `task`: Callable to execute
- `timezone`: Timezone for scheduling
- `dependencies`: List of job IDs this job depends on
- `retry_policy`: Tuple of (max_retries, retry_delay_secs, exponential_backoff)

### Managing Jobs

```python
# Remove a job
scheduler.remove_job("job_id")

# Get job status
status = scheduler.get_job_status("job_id") 

# Get next scheduled run
next_run = scheduler.get_next_run("job_id")

# Start/stop scheduler
scheduler.start()
scheduler.stop()
```

## Job Dependencies

The scheduler allows you to define dependencies between jobs, ensuring jobs run in the correct order:

### How Dependencies Work

1. A job will only run if all its dependent jobs have completed successfully
2. If a dependent job fails, the current job will not execute
3. Dependencies are specified using job IDs
4. Circular dependencies are not supported

### Example

```python
# Define tasks
async def task1():
    print("Processing data...")
    
async def task2():
    print("Generating report...")
    
async def task3():
    print("Sending email...")

# Create jobs with dependencies
job1_id = scheduler.add_job(
    job_type="cron",
    schedule_param="0 0 * * *",  # Daily at midnight
    task=task1,
    timezone="UTC"
)

job2_id = scheduler.add_job(
    job_type="cron", 
    schedule_param="0 1 * * *",  # Daily at 1 AM
    task=task2,
    dependencies=[job1_id]  # Depends on job1
)

# This job depends on both job1 and job2
scheduler.add_job(
    job_type="cron",
    schedule_param="0 2 * * *",  # Daily at 2 AM 
    task=task3,
    dependencies=[job1_id, job2_id]
)
```

In this example:
- task1 runs at midnight
- task2 only runs at 1 AM if task1 completed successfully
- task3 only runs at 2 AM if both task1 and task2 completed successfully


## Retry Policies

Failed jobs can be retried using retry policies:

```python
scheduler.add_job(
    job_type="cron",
    schedule_param="*/5 * * * *",
    task=my_task,
    retry_policy=(
        3,      # Max retries
        60,     # Delay between retries in seconds  
        True    # Use exponential backoff
    )
)
```
