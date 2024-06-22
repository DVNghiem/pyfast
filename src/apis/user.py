# -*- coding: utf-8 -*-
from src.core.endpoint import HTTPEndpoint
from src.factory import Factory
from datetime import datetime
from src.dtos.user import UserDtoResponse


class UserAPI(HTTPEndpoint):
	async def post(self):
		user_helper = await Factory().get_user_helper()
		await user_helper.insert_user(
			{
				'name': 'John Doe',
				'password': '123456',
				'date_of_birth': datetime.now(),
			}
		)
		return 'ok'

	async def get(self) -> UserDtoResponse:
		user_helper = await Factory().get_user_helper()
		items = await user_helper.get_all_users()
		return UserDtoResponse(items=items)
