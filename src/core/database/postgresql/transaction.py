from enum import Enum
from functools import wraps
import traceback
from typing import Callable, Type

from src.core.database.postgresql import session_scope


class Propagation(Enum):
    REQUIRED = "required"
    REQUIRED_NEW = "required_new"


class Transactional:
    def __init__(self, propagation: Propagation = Propagation.REQUIRED):
        self.propagation = propagation

    def __call__(self, function) -> Type[Callable]:
        @wraps(function)
        async def decorator(*args, **kwargs):
            try:
                if self.propagation == Propagation.REQUIRED:
                    result = await self._run_required(
                        function=function,
                        args=args,
                        kwargs=kwargs,
                    )
                elif self.propagation == Propagation.REQUIRED_NEW:
                    result = await self._run_required_new(
                        function=function,
                        args=args,
                        kwargs=kwargs,
                    )
                else:
                    result = await self._run_required(
                        function=function,
                        args=args,
                        kwargs=kwargs,
                    )
            except Exception as exception:
                traceback.print_exc()
                await session_scope.rollback()
                raise exception

            return result

        return decorator

    async def _run_required(self, function, args, kwargs) -> None:
        result = await function(*args, **kwargs)
        await session_scope.commit()
        return result

    async def _run_required_new(self, function, args, kwargs) -> None:
        session_scope.begin()
        result = await function(*args, **kwargs)
        await session_scope.commit()
        return result
