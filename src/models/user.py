# -*- coding: utf-8 -*-
from src.core.database.postgresql import Model
from src.core.database.postgresql.addons import PasswordType, DatetimeType
from sqlalchemy import Column, Integer, String


class User(Model):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String)
	password = Column(PasswordType(max_length=1024, schemes=('bcrypt',)))
	date_of_birth = Column(DatetimeType)

	def __repr__(self):
		return f'<Test {self.name}>'
