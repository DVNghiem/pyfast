from typing import Callable, Optional

from hypern.hypern import WebsocketRoute as WebsocketRouteInternal, WebSocketSession


class WebsocketRoute:
    def __init__(self) -> None:
        self.routes = []
        self._disconnect_handler: Optional[Callable] = None

    def on(self, path):
        def wrapper(func):
            self.routes.append(WebsocketRouteInternal(path, func))
            return func

        return wrapper

    def on_disconnect(self, func):
        """Register a disconnect handler"""
        self._disconnect_handler = func
        return func

    def handle_disconnect(self, session: WebSocketSession):
        """Internal method to handle disconnection"""
        if self._disconnect_handler:
            return self._disconnect_handler(session)
