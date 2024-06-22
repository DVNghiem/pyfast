# -*- coding: utf-8 -*-
from enum import Enum


class ErrorCode(Enum):
	UNKNOWN_ERROR = 'UNKNOWN_ERROR'
	AUTHEN_FAIL = 'AUTHEN_FAIL'
	BAD_REQUEST = 'BAD_REQUEST'
	FORBIDDEN = 'FORBIDDEN'
	SERVER_ERROR = 'SERVER_ERROR'
	NOT_FOUND = 'NOT_FOUND'
	METHOD_NOT_ALLOW = 'METHOD_NOT_ALLOW'
	UNAUTHORIZED = 'UNAUTHORIZED'
	CONFLICT = 'CONFLICT'
	SIGNATURE_VERIFY_FAIL = 'SIGNATURE_VERIFY_FAIL'
	TOKEN_EXPIRED = 'TOKEN_EXPIRED'