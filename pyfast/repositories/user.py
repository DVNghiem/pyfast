# -*- coding: utf-8 -*-

from pyfast.core.database.postgresql import PostgresRepository, Transactional
from pyfast.models import User as UserModel

from typing import Any


class UserRepository(PostgresRepository[UserModel]):
    @Transactional()
    async def insert_user(self, data: dict[str, Any]):
        _user = await self.create(data)
        return _user
