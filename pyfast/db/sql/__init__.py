# -*- coding: utf-8 -*-
from datetime import datetime
from contextvars import ContextVar, Token
from typing import Union, Optional, Dict
import traceback
import threading

from robyn import Request, Response
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.expression import Delete, Insert, Update
from contextlib import asynccontextmanager
from .repository import Model, PostgresRepository
from uuid import uuid4


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
    def __init__(self, DB_URL: str, pool_recycle: int, pool_size: int, max_overflow: int):
        self.DB_URL = DB_URL
        self.pool_recycle = pool_recycle
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        engines = {
            "writer": self.create_engine(),
            "reader": self.create_engine(),
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
            scopefunc=self.session_store.get_context,
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

    def create_engine(self):
        return create_async_engine(self.DB_URL, pool_recycle=self.pool_recycle, pool_size=self.pool_size, max_overflow=self.max_overflow)

    def before_request(self, request: Request):
        token = str(uuid4())
        self.session_store.set_context(token)
        return request

    def after_request(self, response: Response):
        self.session_store.reset_context()
        return response

    def init_app(self, app):
        app.inject_global(get_session=self.get_session)
        app.before_request(endpoint=None)(self.before_request)
        app.after_request(endpoint=None)(self.after_request)


__all__ = ["Model", "PostgresRepository", "SqlConfig"]
