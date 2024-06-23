# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from sqlalchemy.types import TypeDecorator, LargeBinary, String
from base64 import b64encode, b64decode

import os
import typing


class EDEngine(ABC):
	@abstractmethod
	def encrypt(self, data: str) -> str:
		raise NotImplementedError('Method not implemented')

	@abstractmethod
	def decrypt(self, data: str) -> str:
		raise NotImplementedError('Method not implemented')


class AESEngine(EDEngine):
	def __init__(self, secret_key: bytes, iv: bytes, padding_class: typing.Type) -> None:
		super().__init__()
		self.secret_key = secret_key
		self.iv = iv
		self.cipher = Cipher(
			algorithms.AES(self.secret_key), modes.CBC(self.iv), backend=default_backend()
		)
		self.padding = padding_class(128)

	def encrypt(self, data: str) -> str:
		bytes_data = data.encode('utf-8')
		encryptor = self.cipher.encryptor()
		padder = self.padding.padder()
		padded_data = padder.update(bytes_data) + padder.finalize()
		enctyped_data = encryptor.update(padded_data) + encryptor.finalize()
		return b64encode(enctyped_data).decode('utf-8')

	def decrypt(self, data: str) -> str:
		_data = b64decode(data)
		_len_iv = len(self.iv)
		_ciphered_text = _data[_len_iv:]
		unpadder = self.padding.unpadder()
		decryptor = self.cipher.decryptor()
		padded_plain_text = decryptor.update(_ciphered_text) + decryptor.finalize()
		decryptor = self.cipher.decryptor()
		padded_plain_text = decryptor.update(_ciphered_text) + decryptor.finalize()
		return unpadder.update(padded_plain_text) + unpadder.finalize()


class StringEncryptType(TypeDecorator):
	impl = String
	cache_ok = True

	def __init__(self, engine: typing.Optional[EDEngine] = None, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		if not engine:
			key = os.urandom(32)
			iv = os.urandom(16)
			padding_class = padding.PKCS7
			self.engine = AESEngine(secret_key=key, iv=iv, padding_class=padding_class)
		else:
			self.engine = engine  # type: ignore

	def process_bind_param(self, value, dialect):
		if value is None:
			return value
		if not isinstance(value, str):
			raise ValueError('Value String Encrypt Type must be a string')
		return self.engine.encrypt(value)

	def process_result_value(self, value, dialect):
		if value is None:
			return value
		return self.engine.decrypt(value)


class LargeBinaryEncryptType(StringEncryptType):
	impl = LargeBinary
	cache_ok = True

	def __init__(self, engine: typing.Optional[EDEngine] = None, *args, **kwargs) -> None:
		super().__init__(engine=engine, *args, **kwargs)  # type: ignore

	def process_bind_param(self, value, dialect):
		if value is None:
			return value
		value = super().process_bind_param(value, dialect)
		if isinstance(value, str):
			return value.encode('utf-8')
		return value

	def process_result_value(self, value, dialect):
		if isinstance(value, bytes):
			value = value.decode('utf-8')
			return super().process_result_value(value, dialect)
		return value
