from __future__ import annotations

import os

# -*- coding: utf-8 -*-
import threading
import typing
import warnings
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

"""

refer: https://github.com/encode/starlette/blob/master/starlette/config.py
# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

DEBUG = config('DEBUG', cast=bool, default=False)
DATABASE_URL = config('DATABASE_URL')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=CommaSeparatedStrings)
"""


class undefined:
    pass


class EnvironError(Exception):
    pass


class Environ(typing.MutableMapping[str, str]):
    def __init__(self, environ: typing.MutableMapping[str, str] = os.environ):
        self._environ = environ
        self._has_been_read: set[str] = set()

    def __getitem__(self, key: str) -> str:
        self._has_been_read.add(key)
        return self._environ.__getitem__(key)

    def __setitem__(self, key: str, value: str) -> None:
        if key in self._has_been_read:
            raise EnvironError(f"Attempting to set environ['{key}'], but the value has already been read.")
        self._environ.__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        if key in self._has_been_read:
            raise EnvironError(f"Attempting to delete environ['{key}'], but the value has already been read.")
        self._environ.__delitem__(key)

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._environ)

    def __len__(self) -> int:
        return len(self._environ)


environ = Environ()

T = typing.TypeVar("T")


class Config:
    def __init__(
        self,
        env_file: str | Path | None = None,
        environ: typing.Mapping[str, str] = environ,
        env_prefix: str = "",
    ) -> None:
        self.environ = environ
        self.env_prefix = env_prefix
        self.file_values: dict[str, str] = {}
        if env_file is not None:
            if not os.path.isfile(env_file):
                warnings.warn(f"Config file '{env_file}' not found.")
            else:
                self.file_values = self._read_file(env_file)

    @typing.overload
    def __call__(self, key: str, *, default: None) -> str | None: ...

    @typing.overload
    def __call__(self, key: str, cast: type[T], default: T = ...) -> T: ...

    @typing.overload
    def __call__(self, key: str, cast: type[str] = ..., default: str = ...) -> str: ...

    @typing.overload
    def __call__(
        self,
        key: str,
        cast: typing.Callable[[typing.Any], T] = ...,
        default: typing.Any = ...,
    ) -> T: ...

    @typing.overload
    def __call__(self, key: str, cast: type[str] = ..., default: T = ...) -> T | str: ...

    def __call__(
        self,
        key: str,
        cast: typing.Callable[[typing.Any], typing.Any] | None = None,
        default: typing.Any = undefined,
    ) -> typing.Any:
        return self.get(key, cast, default)

    def get(
        self,
        key: str,
        cast: typing.Callable[[typing.Any], typing.Any] | None = None,
        default: typing.Any = undefined,
    ) -> typing.Any:
        key = self.env_prefix + key
        if key in self.environ:
            value = self.environ[key]
            return self._perform_cast(key, value, cast)
        if key in self.file_values:
            value = self.file_values[key]
            return self._perform_cast(key, value, cast)
        if default is not undefined:
            return self._perform_cast(key, default, cast)
        raise KeyError(f"Config '{key}' is missing, and has no default.")

    def _read_file(self, file_name: str | Path) -> dict[str, str]:
        file_values: dict[str, str] = {}
        with open(file_name) as input_file:
            for line in input_file.readlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    file_values[key] = value
        return file_values

    def _perform_cast(
        self,
        key: str,
        value: typing.Any,
        cast: typing.Callable[[typing.Any], typing.Any] | None = None,
    ) -> typing.Any:
        if cast is None or value is None:
            return value
        elif cast is bool and isinstance(value, str):
            mapping = {"true": True, "1": True, "false": False, "0": False}
            value = value.lower()
            if value not in mapping:
                raise ValueError(f"Config '{key}' has value '{value}'. Not a valid bool.")
            return mapping[value]
        try:
            return cast(value)
        except (TypeError, ValueError):
            raise ValueError(f"Config '{key}' has value '{value}'. Not a valid {cast.__name__}.")


class ContextStore:
    def __init__(self, cleanup_interval: int = 300, max_age: int = 3600):
        """
        Initialize ContextStore with automatic session cleanup.

        :param cleanup_interval: Interval between cleanup checks (in seconds)
        :param max_age: Maximum age of a session before it's considered expired (in seconds)
        """
        self._session_times: Dict[str, datetime] = {}
        self.session_var = ContextVar("session_id", default=None)

        self._max_age = max_age
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Start the cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start a background thread for periodic session cleanup."""

        def cleanup_worker():
            while not self._stop_event.is_set():
                self._perform_cleanup()
                self._stop_event.wait(self._cleanup_interval)

        self._cleanup_thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,  # Allows the thread to be automatically terminated when the main program exits
        )
        self._cleanup_thread.start()

    def _perform_cleanup(self):
        """Perform cleanup of expired sessions."""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, timestamp in list(self._session_times.items()) if (current_time - timestamp).total_seconds() > self._max_age
        ]

        for session_id in expired_sessions:
            self.remove_session(session_id)

    def remove_session(self, session_id: str):
        """Remove a specific session."""
        self._session_times.pop(session_id, None)

    def set_context(self, session_id: str):
        """
        Context manager for setting and resetting session context.

        :param session_id: Unique identifier for the session
        :return: Context manager for session
        """
        self.session_var.set(session_id)
        self._session_times[session_id] = datetime.now()

    def get_context(self) -> str:
        """
        Get the current session context.

        :return: Current session ID
        :raises RuntimeError: If no session context is available
        """
        return self.session_var.get()

    def reset_context(self):
        """Reset the session context."""
        token = self.get_context()
        if token is not None:
            self.session_var.reset(token)

    def stop_cleanup(self):
        """
        Stop the cleanup thread.
        Useful for graceful shutdown of the application.
        """
        self._stop_event.set()
        if self._cleanup_thread:
            self._cleanup_thread.join()

    def __del__(self):
        """
        Ensure cleanup thread is stopped when the object is deleted.
        """
        self.stop_cleanup()


context_store = ContextStore()
