from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any, List, Tuple, Dict

@dataclass
class BaseBackend:
    get: Callable[[str], Any]
    set: Callable[[Any, str, int], None]
    delete_startswith: Callable[[str], None]

@dataclass
class RedisBackend(BaseBackend):
    url: str

    get: Callable[[str], Any]
    set: Callable[[Any, str, int], None]
    delete_startswith: Callable[[str], None]

@dataclass
class BaseSchemaGenerator:
    remove_converter: Callable[[str], str]
    parse_docstring: Callable[[Callable[..., Any]], str]

@dataclass
class SwaggerUI:
    title: str
    openapi_url: str

    render_template: Callable[..., Any]
    get_html_content: Callable[..., str]

@dataclass
class BackgroundTask:
    """
    A task to be executed in the background
    id: str: The task ID
    function: Callable[..., Any]: The function to be executed
    args: List | Tuple: The arguments to be passed to the function
    kwargs: Dict[str, Any]: The keyword arguments to be passed to the function
    timeout_secs: int: The maximum time in seconds the task is allowed to run
    cancelled: bool: Whether the task is cancelled

    **Note**: function is currently running with sync mode, so it should be a sync function
    """

    id: str
    function: Callable[..., Any]
    args: List | Tuple
    kwargs: Dict[str, Any]
    timeout_secs: int
    cancelled: bool

    def get_id(self) -> str:
        """
        Get the task ID
        """
        pass

    def cancel(self) -> None:
        """
        Cancel the task
        """
        pass

    def is_cancelled(self) -> bool:
        """
        Check if the task is cancelled
        """
        pass

    def execute(self) -> Any:
        """
        Execute the task
        """
        pass

@dataclass
class BackgroundTasks:
    """
    A collection of tasks to be executed in the background

    **Note**: Only set tasks. pool, sender, receiver are set by the framework
    """

    def add_task(self, task: BackgroundTask) -> str:
        """
        Add a task to the collection
        """
        pass

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task in the collection
        """
        pass

    def execute_all(self) -> None:
        """
        Execute all tasks in the collection
        """
        pass

    def execute_task(self, task_id: str) -> None:
        """
        Execute a task in the collection
        """
        pass

class Scheduler:
    def add_job(
        self,
        job_type: str,
        schedule_param: str,
        task: Callable[..., Any],
        timezone: str,
        dependencies: List[str],
        retry_policy: Tuple[int, int, bool] | None = None,
    ) -> str:
        """
        Add a job to the scheduler
        params:
        job_type: str: The type of the job (e.g. "cron", "interval")

        schedule_param: str: The schedule parameter of the job. interval in seconds for interval jobs, cron expression for cron jobs

        Exmaple:
        //           sec  min   hour   day of month   month   day of week   year
        expression = "0   30   9,12,15     1,15       May-Aug  Mon,Wed,Fri  2018/2";

        task: Callable[..., Any]: The task to be executed

        timezone: str: The timezone of the job

        dependencies: List[str]: The IDs of the jobs this job depends on

        retry_policy: Tuple[int, int, bool] | None: The retry policy of the job. (max_retries, retry_delay_secs, exponential_backoff)

        return:
        str: The ID of the job
        """
        pass

    def remove_job(self, job_id: str) -> None:
        """
        Remove a job from the scheduler
        """
        pass

    def start(self) -> None:
        """
        Start the scheduler
        """
        pass

    def stop(self) -> None:
        """
        Stop the scheduler
        """
        pass

    def get_job_status(self, job_id: str) -> Tuple[float, float, List[str], int]:
        """
        Get the status of a job
        """
        pass

    def get_next_run(self, job_id: str) -> float:
        """
        Get the next run time of a job
        """
        pass
