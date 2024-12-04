# Scheduler Documentation

## Overview
The scheduler component provides a flexible way to schedule and manage periodic tasks in your application. It supports both interval-based and cron-based scheduling with features like task dependencies and retry policies.

## Installation
The scheduler is included in the Hypern framework. No additional installation is required.

## Basic Usage

### Initialize the Scheduler
```python
from hypern.scheduler import Scheduler

scheduler = Scheduler()
```

### Adding Jobs

#### Interval Jobs
```python
# Schedule a task to run every 60 seconds
scheduler.add_job(
    job_type="interval",
    schedule_param="60",  # seconds
    task=lambda: print("Running every minute"),
    timezone="UTC",
    dependencies=[]
)
```

#### Cron Jobs
```python
# Schedule a task using cron expression
scheduler.add_job(
    job_type="cron",
    schedule_param="0 */1 * * * * *",  # Every hour
    task=lambda: print("Running hourly"),
    timezone="UTC",
    dependencies=[]
)
```

### Adding Scheduler to Application
```python
from hypern import Hypern

app = Hypern(
    scheduler=scheduler,
    routes=[...]
)
```

## Advanced Features

### Retry Policies
```python
# Add job with retry policy
scheduler.add_job(
    job_type="interval",
    schedule_param="300",  # 5 minutes
    task=my_task,
    timezone="UTC",
    dependencies=[],
    retry_policy=(3, 60, True)  # max_retries, retry_delay_secs, exponential_backoff
)
```

### Job Dependencies
```python
# Create jobs with dependencies
job1_id = scheduler.add_job(
    job_type="interval",
    schedule_param="60",
    task=task1,
    timezone="UTC",
    dependencies=[]
)

scheduler.add_job(
    job_type="interval",
    schedule_param="60",
    task=task2,
    timezone="UTC",
    dependencies=[job1_id]  # task2 will only run after task1 completes
)
```

### Job Management

```python
# Remove a job
scheduler.remove_job(job_id)

# Get job status
status = scheduler.get_job_status(job_id)

# Get next scheduled run
next_run = scheduler.get_next_run(job_id)
```

## Cron Expression Format
The cron expression follows the format: `second minute hour day_of_month month day_of_week year`

Example patterns:
- `0 0 * * * * *` - Every hour
- `0 */15 * * * * *` - Every 15 minutes
- `0 0 0 * * * *` - Every day at midnight

## Timezone Support
The scheduler supports all standard timezone names from the `chrono_tz` library. Always specify the timezone when creating jobs to ensure correct scheduling across different time zones.

## Best Practices
1. Use meaningful task names and logging
2. Set appropriate retry policies for critical tasks
3. Consider dependencies when scheduling related tasks
4. Monitor job execution status regularly
5. Use appropriate timezone settings for your use case
