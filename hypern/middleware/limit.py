from typing import Optional
import time
from abc import ABC, abstractmethod
from threading import Lock

from hypern.hypern import Request, Response

from .base import Middleware, MiddlewareConfig


class StorageBackend(ABC):
    @abstractmethod
    def increment(self, key, amount=1, expire=None):
        pass

    @abstractmethod
    def get(self, key):
        pass


class RedisBackend(StorageBackend):
    def __init__(self, redis_client):
        self.redis = redis_client

    def increment(self, key, amount=1, expire=None):
        """
        The `increment` function increments a value in Redis by a specified amount and optionally sets an
        expiration time for the key.

        :param key: The `key` parameter in the `increment` method is used to specify the key in the Redis
        database that you want to increment
        :param amount: The `amount` parameter in the `increment` method specifies the value by which the
        key's current value should be incremented. By default, it is set to 1, meaning that if no specific
        amount is provided, the key's value will be incremented by 1, defaults to 1 (optional)
        :param expire: The `expire` parameter in the `increment` method is used to specify the expiration
        time for the key in Redis. If a value is provided for `expire`, the key will expire after the
        specified number of seconds. If `expire` is not provided (i.e., it is `None`
        :return: The `increment` method returns the result of incrementing the value of the key by the
        specified amount. If an expiration time is provided, it also sets the expiration time for the key in
        Redis. The method returns the updated value of the key after the increment operation.
        """
        with self.redis.pipeline() as pipe:
            pipe.incr(key, amount)
            if expire:
                pipe.expire(key, int(expire))
            return pipe.execute()[0]

    def get(self, key):
        return int(self.redis.get(key) or 0)


class InMemoryBackend(StorageBackend):
    def __init__(self):
        self.storage = {}

    def increment(self, key, amount=1, expire=None):
        """
        The `increment` function updates the value associated with a key in a storage dictionary by a
        specified amount and optionally sets an expiration time.

        :param key: The `key` parameter in the `increment` method is used to identify the value that needs
        to be incremented in the storage. It serves as a unique identifier for the value being manipulated
        :param amount: The `amount` parameter in the `increment` method specifies the value by which the
        existing value associated with the given `key` should be incremented. By default, if no `amount` is
        provided, it will increment the value by 1, defaults to 1 (optional)
        :param expire: The `expire` parameter in the `increment` method is used to specify the expiration
        time for the key-value pair being incremented. If a value is provided for the `expire` parameter, it
        sets the expiration time for the key in the storage dictionary to the current time plus the
        specified expiration duration
        :return: The function `increment` returns the updated value of the key in the storage after
        incrementing it by the specified amount.
        """
        if key not in self.storage:
            self.storage[key] = {"value": 0, "expire": None}
        self.storage[key]["value"] += amount
        if expire:
            self.storage[key]["expire"] = time.time() + expire
        return self.storage[key]["value"]

    def get(self, key):
        """
        This Python function retrieves the value associated with a given key from a storage dictionary,
        checking for expiration before returning the value or 0 if the key is not found.

        :param key: The `key` parameter is used to specify the key of the item you want to retrieve from the
        storage. The function checks if the key exists in the storage dictionary and returns the
        corresponding value if it does. If the key has an expiration time set and it has expired, the
        function deletes the key
        :return: The `get` method returns the value associated with the given key if the key is present in
        the storage and has not expired. If the key is not found or has expired, it returns 0.
        """
        if key in self.storage:
            if self.storage[key]["expire"] and time.time() > self.storage[key]["expire"]:
                del self.storage[key]
                return 0
            return self.storage[key]["value"]
        return 0


class RateLimitMiddleware(Middleware):
    """
    The RateLimitMiddleware class implements rate limiting functionality to restrict the number of
    Requests per minute for a given IP address.
    """

    def __init__(self, storage_backend, config: Optional[MiddlewareConfig] = None, requests_per_minute=60, window_size=60):
        super().__init__(config)
        self.storage = storage_backend
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size

    def get_request_identifier(self, request: Request):
        return request.remote_addr

    def before_request(self, request: Request):
        """
        The `before_request` function checks the request rate limit and returns a 429 status code if the
        limit is exceeded.

        :param request: The `request` parameter in the `before_request` method is of type `Request`. It
        is used to represent an incoming HTTP request that the server will process
        :type request: Request
        :return: The code snippet is a method called `before_request` that takes in a `Request` object
        as a parameter.
        """
        identifier = self.get_request_identifier(request)
        current_time = int(time.time())
        window_key = f"{identifier}:{current_time // self.window_size}"

        request_count = self.storage.increment(window_key, expire=self.window_size)

        if request_count > self.requests_per_minute:
            return Response(status_code=429, description=b"Too Many Requests", headers={"Retry-After": str(self.window_size)})

        return request

    def after_request(self, response):
        return response


class ConcurrentRequestMiddleware(Middleware):
    # The `ConcurrentRequestMiddleware` class limits the number of concurrent requests and returns a 429
    # status code with a Retry-After header if the limit is reached.
    def __init__(self, max_concurrent_requests=100):
        super().__init__()
        self.max_concurrent_requests = max_concurrent_requests
        self.current_requests = 0
        self.lock = Lock()

    def get_request_identifier(self, request):
        return request.remote_addr

    def before_request(self, request):
        """
        The `before_request` function limits the number of concurrent requests and returns a 429 status code
        with a Retry-After header if the limit is reached.

        :param request: The `before_request` method in the code snippet is a method that is called before
        processing each incoming request. It checks if the number of current requests is within the allowed
        limit (`max_concurrent_requests`). If the limit is exceeded, it returns a 429 status code with a
        "Too Many Requests
        :return: the `request` object after checking if the number of current requests is within the allowed
        limit. If the limit is exceeded, it returns a 429 status code response with a "Too Many Requests"
        description and a "Retry-After" header set to 5.
        """

        with self.lock:
            if self.current_requests >= self.max_concurrent_requests:
                return Response(status_code=429, description="Too Many Requests", headers={"Retry-After": "5"})
            self.current_requests += 1

        return request

    def after_request(self, response):
        with self.lock:
            self.current_requests -= 1
        return response
