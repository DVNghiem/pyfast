from abc import ABC, abstractmethod
from robyn import Response, Request


# The `Middleware` class is an abstract base class with abstract methods `before_request` and
# `after_request` for handling requests and responses in a web application.
class Middleware(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.app = None

    @abstractmethod
    def before_request(self, request: Request):
        pass

    @abstractmethod
    def after_request(self, response: Response):
        pass
