# -*- coding: utf-8 -*-
import asyncio
import threading
from datetime import datetime
from typing import Optional

from hypern.hypern import DatabaseTransaction, Request, Response, DatabaseType
from weakref import WeakKeyDictionary

database_connection = None


class SqlConfig:
    def __init__(self, driver: DatabaseType, url: str, max_connections: int = 10, min_connections: int = 1, idle_timeout: int = 30, **kwargs) -> None:
        global database_connection

    async def before_request(self, request: Request):
        print("before_request")
        # print(transaction.fetch_all("SELECT 1", []))
        return request

    async def after_request(self, response: Response):
        return response

    def init_app(self, app):
        app.before_request()(self.before_request)
        app.after_request()(self.after_request)


class DatabaseContextStore:
    _stop_event = threading.Event()

    def __init__(self, cleanup_interval: int = 300, max_age: int = 20):
        """
        Initialize ContextStore with automatic session cleanup.

        :param cleanup_interval: Interval between cleanup checks (in seconds)
        :param max_age: Maximum age of a session before it's considered expired (in seconds)
        """
        self._session_times = WeakKeyDictionary()
        self.session_var = WeakKeyDictionary()

        self._max_age = max_age
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: Optional[threading.Thread] = None

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

    def get_or_create_session(self) -> DatabaseTransaction:
        global database_connection

        current_task = asyncio.current_task()
        print("current_task", current_task)

        if current_task not in self.session_var:
            print("create new session")
            transaction = database_connection.transaction()
            self.session_var[current_task] = transaction
            self._session_times[current_task] = datetime.now()
            # current_task.add_done_callback(lambda t: self.cleanup_session(current_task))
        print("return session")
        return self.session_var[current_task]

    def cleanup_session(self, task):
        sessions = self.session_var.get(task)
        if sessions:
            try:
                sessions.commit()
            except Exception:
                sessions.rollback()
            finally:
                del self.session_var[task]

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


db_context_store = DatabaseContextStore()
