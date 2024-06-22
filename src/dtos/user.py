# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict


class UserDtoResponseItem(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	name: str
	date_of_birth: float


class UserDtoResponse(BaseModel):
	items: list[UserDtoResponseItem]
