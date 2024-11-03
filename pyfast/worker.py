# -*- coding: utf-8 -*-
from typing import Any
from celery import Celery
from asgiref.sync import async_to_sync


class AsyncCelery(Celery):
    def __new__(cls, *args, **kwargs) -> Any:
        if not hasattr(cls, "instance") or not cls.instance:  # type: ignore
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.patch_task()

    def patch_task(self) -> None:
        TaskBase = self.Task

        class ContextTask(TaskBase):  # type: ignore
            abstract = True

            def _run(self, *args, **kwargs):
                result = async_to_sync(TaskBase.__call__)(self, *args, **kwargs)
                return result

            def __call__(self, *args, **kwargs):
                return self._run(*args, **kwargs)

        self.Task = ContextTask
