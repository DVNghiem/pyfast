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

    def get_html_content(self) -> str: ...

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

@dataclass
class FunctionInfo:
    """
    The function info object passed to the route handler.

    Attributes:
        handler (Callable): The function to be called
        is_async (bool): Whether the function is async or not
        number_of_params (int): The number of parameters the function has
        args (dict): The arguments of the function
        kwargs (dict): The keyword arguments of the function
    """

    handler: Callable
    is_async: bool
    number_of_params: int
    args: dict
    kwargs: dict

class SocketHeld:
    socket: Any

class Server:
    router: Router
    websocket_router: Any
    startup_handler: Any
    shutdown_handler: Any
    excluded_response_headers_paths: Any

    def add_route(self, route: Route) -> None: ...
    def set_router(self, router: Router) -> None: ...
    def start(self, socket: SocketHeld, worker: int, processes: int) -> None: ...

class Route:
    path: str
    function: FunctionInfo
    method: str

    def matches(self, path: str, method: str) -> str: ...
    def clone_route(self) -> Route: ...
    def update_path(self, new_path: str) -> None: ...
    def update_method(self, new_method: str) -> None: ...
    def is_valid(self) -> bool: ...
    def get_path_parans(self) -> List[str]: ...
    def has_parameters(self) -> bool: ...
    def normalized_path(self) -> str: ...
    def same_handler(self, other: Route) -> bool: ...

class Router:
    routes: List[Route]

    def add_route(self, route: Route) -> None: ...
    def remove_route(self, path: str, method: str) -> bool: ...
    def get_route(self, path: str, method) -> Route | None: ...
    def get_routes_by_path(self, path: str) -> List[Route]: ...
    def get_routes_by_method(self, method: str) -> List[Route]: ...
    def extend_route(self, routes: List[Route]) -> None: ...

@dataclass
class Header:
    headers: Dict[str, str]

@dataclass
class Response:
    status_code: int
    response_type: str
    headers: Any
    description: str
    file_path: str

@dataclass
class QueryParams:
    queries: Dict[str, List[str]]

@dataclass
class UploadedFile:
    name: str
    content_type: str
    path: str
    size: int
    content: bytes
    filename: str

@dataclass
class BodyData:
    json: bytes
    files: List[UploadedFile]

@dataclass
class Request:
    query_params: QueryParams
    headers: Dict[str, str]
    path_params: Dict[str, str]
    body: BodyData
    method: str