from .hypern import WebsocketRoute as WebsocketRouteInternal, WebSocketSession


class WebsocketRoute:
    def __init__(self) -> None:
        self.routes = []

    def on(self, path):
        def wrapper(func):
            self.routes.append(WebsocketRouteInternal(path, func))
            return func

        return wrapper


__all__ = ["WebsocketRoute", "WebSocketSession"]
