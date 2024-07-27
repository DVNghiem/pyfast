# -*- coding: utf-8 -*-
from pyfast.core.database.postgresql import get_session
from pyfast.repositories import UserRepository
from pyfast.models import User
from pyfast.helper import UserHelper
from functools import partial


class Factory:
    # Repositories
    user_repository = partial(UserRepository, User)

    async def get_user_helper(self):
        async with get_session() as session:
            return UserHelper(user_repository=self.user_repository(db_session=session))
