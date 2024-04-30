# -*- coding: utf-8 -*-
from typing import Any
from src.enum import ErrorCode


class BaseException(Exception):
	def __init__(self, msg: str = '', *args: Any) -> None:
		super().__init__(*args)
		self.msg = msg
		self.status = 400
		self.errors: list = []
		self.error_code = ErrorCode.UNKNOWN_ERROR.name


class BadRequest(BaseException):
	def __init__(
		self,
		msg: str = 'Bad request',
		errors: list = [],
		error_code: str = ErrorCode.BAD_REQUEST.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.error_code = error_code


class Forbidden(BaseException):
	def __init__(
		self,
		msg: str = 'Forbidden',
		errors: list = [],
		error_code: str = ErrorCode.FORBIDDEN.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 403
		self.error_code = error_code


class NotFound(BaseException):
	def __init__(
		self,
		msg: str = 'NotFound',
		errors: list = [],
		error_code: str = ErrorCode.NOT_FOUND.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 404
		self.error_code = error_code


class MethodNotAllow(BaseException):
	def __init__(
		self,
		msg: str = 'Method not allow',
		error_code: str = ErrorCode.METHOD_NOT_ALLOW.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.status = 405
		self.error_code = error_code


class ConflictError(BaseException):
	def __init__(
		self,
		msg: str = 'Conflict',
		errors: list = [],
		error_code: str = ErrorCode.CONFLICT.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 409
		self.error_code = error_code


class InternalServer(BaseException):
	def __init__(
		self,
		msg: str = 'Internal server error',
		errors: list = [],
		error_code: str = ErrorCode.SERVER_ERROR.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 500
		self.error_code = error_code


class Unauthorized(BaseException):
	def __init__(
		self,
		msg: str = 'Unauthorized',
		errors: list = [],
		error_code: str = ErrorCode.UNAUTHORIZED.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 401
		self.error_code = error_code


class SignatureVerifyFail(BaseException):
	def __init__(
		self,
		msg: str = 'Signature verify fail',
		errors: list = [],
		error_code: str = ErrorCode.SIGNATURE_VERIFY_FAIL.name,
		*args: Any,
	) -> None:
		super().__init__(msg, *args)
		self.errors = errors
		self.status = 409
		self.error_code = error_code
