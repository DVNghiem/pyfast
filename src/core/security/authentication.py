from starlette.requests import Request
from src.enum import ErrorCode
from src.core.exception import Forbidden
from abc import ABC, abstractmethod
from src.core.logger import logger
from src.config import config
import datetime
import jwt
import traceback
import typing


class Authorization(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.auth_data = None
        self.name = "base"

    @abstractmethod
    def validate(self, request: Request, *arg, **kwargs) -> typing.Any:
        pass


class JsonWebToken(Authorization):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super(JsonWebToken, self).__init__(*args, **kwargs)
        self.access_key = config.ACCESS_TOKEN
        self.refresh_key = config.ACCESS_TOKEN
        self.algorithm = config.ALGORITHM
        self.name = "bearerAuth"

    def create_token(
        self, payload_data, *arg: typing.Any, **kwargs: typing.Any
    ) -> typing.Dict:
        token = jwt.encode(
            payload={
                "payload": payload_data,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60 * 5),
            },
            key=self.access_key,
            algorithm=self.algorithm,
        )
        return {
            "access_token": token,
        }

    async def validate(
        self, request: Request, *arg: typing.Any, **kwargs: typing.Any
    ) -> typing.Dict:
        super(JsonWebToken, self).validate(request, *arg, **kwargs)
        _token = ""
        try:
            _authorization = request.headers.get("authorization")
            if not _authorization:
                raise
            _type, _token = _authorization.split()
            if _type.lower() != "bearer":
                raise
            _decode = jwt.decode(
                _token, key=self.access_key, algorithms=[self.algorithm]
            )
            _payload = _decode.get("payload", {})
            return _payload
        except jwt.exceptions.ExpiredSignatureError:
            raise Forbidden(
                msg="Token is expired", error_code=ErrorCode.TOKEN_EXPIRED.name
            )
        except Exception as e:
            logger.debug(e)
            raise Forbidden(msg="Authen Fail", error_code=ErrorCode.AUTHEN_FAIL.name)


class APIKeyAuthen(Authorization):
    def __init__(self) -> None:
        super().__init__()

    async def validate(
        self, request: Request, *arg: typing.Any, **kwargs: typing.Any
    ) -> typing.Dict:
        try:
            api_db = request.state._state.get("api_key")
            if api_db is None:
                logger.info("api db not set")
                raise
            api_key = request.headers.get("authorization")
            _data = await api_db.find_one({"api_key": api_key})
            if not _data:
                logger.info("===== error api_key =====")
                logger.info(api_key)
                logger.info(_data)
                raise Exception()
            return _data
        except Exception:
            traceback.print_exc()
            raise Forbidden()
