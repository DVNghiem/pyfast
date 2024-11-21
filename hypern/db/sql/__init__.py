# -*- coding: utf-8 -*-
import asyncio
import threading
import traceback
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from datetime import datetime
from typing import Dict, Optional, Union
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_scoped_session
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.expression import Delete, Insert, Update

from hypern.hypern import Request, Response

from .repository import Model, PostgresRepository


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


class SqlConfig:
    def __init__(self, default_engine: AsyncEngine | None = None, reader_engine: AsyncEngine | None = None, writer_engine: AsyncEngine | None = None):
        """
        Initialize the SQL configuration.
        You can provide a default engine, a reader engine, and a writer engine.
        If only one engine is provided (default_engine), it will be used for both reading and writing.
        If both reader and writer engines are provided, they will be used for reading and writing respectively.
        Note: The reader and writer engines must be different.
        """

        assert default_engine or reader_engine or writer_engine, "At least one engine must be provided."
        assert not (reader_engine and writer_engine and id(reader_engine) == id(writer_engine)), "Reader and writer engines must be different."

        engines = {
            "writer": writer_engine or default_engine,
            "reader": reader_engine or default_engine,
        }
        self.session_store = ContextStore()

        class RoutingSession(Session):
            def get_bind(this, mapper=None, clause=None, **kwargs):
                if this._flushing or isinstance(clause, (Update, Delete, Insert)):
                    return engines["writer"].sync_engine
                return engines["reader"].sync_engine

        async_session_factory = sessionmaker(
            class_=AsyncSession,
            sync_session_class=RoutingSession,
            expire_on_commit=False,
        )

        session_scope: Union[AsyncSession, async_scoped_session] = async_scoped_session(
            session_factory=async_session_factory,
            scopefunc=asyncio.current_task,
        )

        @asynccontextmanager
        async def get_session():
            """
            Get the database session.
            This can be used for dependency injection.

            :return: The database session.
            """
            try:
                yield session_scope
            except Exception:
                traceback.print_exc()
                await session_scope.rollback()
            finally:
                await session_scope.remove()
                await session_scope.close()

        self.get_session = get_session
        self._context_token: Optional[Token] = None

    def before_request(self, request: Request):
        token = str(uuid4())
        self.session_store.set_context(token)
        return request

    def after_request(self, response: Response):
        self.session_store.reset_context()
        return response

    def init_app(self, app):
        app.inject("get_session", self.get_session)
        app.before_request()(self.before_request)
        app.after_request()(self.after_request)


__all__ = ["Model", "PostgresRepository", "SqlConfig"]
