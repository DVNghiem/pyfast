# -*- coding: utf-8 -*-
from typing import Any
from hypern.enum import ErrorCode


class BaseException(Exception):
    def __init__(self, msg: str = "", *args: Any) -> None:
        super().__init__(*args)
        self.msg = msg
        self.status = 400
        self.error_code = ErrorCode.UNKNOWN_ERROR


class BadRequest(BaseException):
    def __init__(
        self,
        msg: str = "Bad request",
        error_code: str = ErrorCode.BAD_REQUEST,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.error_code = error_code


class ValidationError(BaseException):
    def __init__(
        self,
        msg: str = "Validation error",
        error_code: str = ErrorCode.VALIDATION_ERROR,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.error_code = error_code


class Forbidden(BaseException):
    def __init__(
        self,
        msg: str = "Forbidden",
        error_code: str = ErrorCode.FORBIDDEN,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.status = 403
        self.error_code = error_code


class NotFound(BaseException):
    def __init__(
        self,
        msg: str = "NotFound",
        error_code: str = ErrorCode.NOT_FOUND,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.status = 404
        self.error_code = error_code


class MethodNotAllow(BaseException):
    def __init__(
        self,
        msg: str = "Method not allow",
        error_code: str = ErrorCode.METHOD_NOT_ALLOW,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.status = 405
        self.error_code = error_code


class InternalServer(BaseException):
    def __init__(
        self,
        msg: str = "Internal server error",
        error_code: str = ErrorCode.SERVER_ERROR,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.status = 500
        self.error_code = error_code


class Unauthorized(BaseException):
    def __init__(
        self,
        msg: str = "Unauthorized",
        error_code: str = ErrorCode.UNAUTHORIZED,
        *args: Any,
    ) -> None:
        super().__init__(msg, *args)
        self.status = 401
        self.error_code = error_code


class InvalidPortNumber(Exception):
    pass
