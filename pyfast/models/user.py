# -*- coding: utf-8 -*-
from pyfast.core.database.postgresql import Model
from pyfast.core.database.postgresql.addons import (
    PasswordType,
    DatetimeType,
    StringEncryptType,
    LargeBinaryEncryptType,
    AESEngine,
)
from sqlalchemy import Column, Integer, String
from cryptography.hazmat.primitives.padding import PKCS7
import os

aes_engine = AESEngine(secret_key=os.urandom(32), iv=os.urandom(16), padding_class=PKCS7)


class User(Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    password = Column(PasswordType(max_length=1024, schemes=("bcrypt",)))
    date_of_birth = Column(DatetimeType)
    encrypt_1 = Column(StringEncryptType(engine=aes_engine))
    encrypt_2 = Column(LargeBinaryEncryptType(engine=aes_engine))

    def __repr__(self):
        return f"<Test {self.name}>"
