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
