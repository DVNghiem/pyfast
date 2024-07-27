# -*- coding: utf-8 -*-
from pyfast.repositories import UserRepository


class UserHelper:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def insert_user(self, data: dict):
        return await self.user_repository.insert_user(data)

    async def get_all_users(self):
        return await self.user_repository.get_all()
