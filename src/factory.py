# -*- coding: utf-8 -*-
from src.core.database.postgresql import get_session
from src.repositories import UserRepository
from src.models import User
from src.helper import UserHelper
from functools import partial


class Factory:
	# Repositories
	user_repository = partial(UserRepository, User)

	async def get_user_helper(self):
		async with get_session() as session:
			return UserHelper(user_repository=self.user_repository(db_session=session))
