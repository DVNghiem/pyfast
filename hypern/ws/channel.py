from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Set

from hypern.hypern import WebSocketSession


@dataclass
class Channel:
    name: str
    subscribers: Set[WebSocketSession] = field(default_factory=set)
    handlers: Dict[str, Callable[[WebSocketSession, Any], Awaitable[None]]] = field(default_factory=dict)

    def publish(self, event: str, data: Any, publisher: WebSocketSession = None):
        """Publish an event to all subscribers except the publisher"""
        for subscriber in self.subscribers:
            if subscriber != publisher:
                subscriber.send({"channel": self.name, "event": event, "data": data})

    def handle_event(self, event: str, session: WebSocketSession, data: Any):
        """Handle an event on this channel"""
        if event in self.handlers:
            self.handlers[event](session, data)

    def add_subscriber(self, subscriber: WebSocketSession):
        """Add a subscriber to the channel"""
        self.subscribers.add(subscriber)

    def remove_subscriber(self, subscriber: WebSocketSession):
        """Remove a subscriber from the channel"""
        self.subscribers.discard(subscriber)

    def on(self, event: str):
        """Decorator for registering event handlers"""

        def decorator(handler: Callable[[WebSocketSession, Any], Awaitable[None]]):
            self.handlers[event] = handler
            return handler

        return decorator


class ChannelManager:
    def __init__(self):
        self.channels: Dict[str, Channel] = {}
        self.client_channels: Dict[WebSocketSession, Set[str]] = {}

    def create_channel(self, channel_name: str) -> Channel:
        """Create a new channel if it doesn't exist"""
        if channel_name not in self.channels:
            self.channels[channel_name] = Channel(channel_name)
        return self.channels[channel_name]

    def get_channel(self, channel_name: str) -> Channel:
        """Get a channel by name"""
        return self.channels.get(channel_name)

    def subscribe(self, client: WebSocketSession, channel_name: str):
        """Subscribe a client to a channel"""
        channel = self.create_channel(channel_name)
        channel.add_subscriber(client)

        if client not in self.client_channels:
            self.client_channels[client] = set()
        self.client_channels[client].add(channel_name)

    def unsubscribe(self, client: WebSocketSession, channel_name: str):
        """Unsubscribe a client from a channel"""
        channel = self.get_channel(channel_name)
        if channel:
            channel.remove_subscriber(client)
            if client in self.client_channels:
                self.client_channels[client].discard(channel_name)

    def unsubscribe_all(self, client: WebSocketSession):
        """Unsubscribe a client from all channels"""
        if client in self.client_channels:
            channels = self.client_channels[client].copy()
            for channel_name in channels:
                self.unsubscribe(client, channel_name)
            del self.client_channels[client]
