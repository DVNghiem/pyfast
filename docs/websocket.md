# WebSocket Documentation

## Overview

This document provides an overview of the WebSocket implementation in the project. It covers the main components and their interactions, including WebSocket sessions, rooms, channels, and routes.

## Components

### WebSocketSession

The `WebSocketSession` class represents a WebSocket connection. It provides methods to send messages and close the connection.

#### Methods

- `new() -> Self`: Creates a new WebSocket session.
- `send(&self, message: &PyAny) -> PyResult<()>`: Sends a message through the WebSocket.
- `close(&self) -> PyResult<()>`: Closes the WebSocket connection.


### WebsocketRoute

The `WebsocketRoute` class manages WebSocket routes.

#### Methods

- `on(self, path)`: Registers a WebSocket route.


### Room

The `Room` class manages a group of WebSocket clients. It allows broadcasting messages to all clients in the room.

#### Methods

- `broadcast(self, message: str, exclude: WebSocketSession = None)`: Broadcasts a message to all clients in the room except the excluded one.
- `add_client(self, client: WebSocketSession)`: Adds a client to the room.
- `remove_client(self, client: WebSocketSession)`: Removes a client from the room.
- `client_count(self) -> int`: Returns the number of clients in the room.

### RoomManager

The `RoomManager` class manages multiple rooms and their clients.

#### Methods

- `create_room(self, room_name: str) -> Room`: Creates a new room if it doesn't exist.
- `get_room(self, room_name: str) -> Room`: Gets a room by name.
- `join_room(self, client: WebSocketSession, room_name: str)`: Adds a client to a room.
- `leave_room(self, client: WebSocketSession, room_name: str)`: Removes a client from a room.
- `leave_all_rooms(self, client: WebSocketSession)`: Removes a client from all rooms.

### Channel

The `Channel` class manages a group of WebSocket subscribers and handles events.

#### Methods

- `publish(self, event: str, data: Any, publisher: WebSocketSession = None)`: Publishes an event to all subscribers except the publisher.
- `handle_event(self, event: str, session: WebSocketSession, data: Any)`: Handles an event on the channel.
- `add_subscriber(self, subscriber: WebSocketSession)`: Adds a subscriber to the channel.
- `remove_subscriber(self, subscriber: WebSocketSession)`: Removes a subscriber from the channel.
- `on(self, event: str)`: Decorator for registering event handlers.

### ChannelManager

The `ChannelManager` class manages multiple channels and their subscribers.

#### Methods

- `create_channel(self, channel_name: str) -> Channel`: Creates a new channel if it doesn't exist.
- `get_channel(self, channel_name: str) -> Channel`: Gets a channel by name.
- `subscribe(self, client: WebSocketSession, channel_name: str)`: Subscribes a client to a channel.
- `unsubscribe(self, client: WebSocketSession, channel_name: str)`: Unsubscribes a client from a channel.
- `unsubscribe_all(self, client: WebSocketSession)`: Unsubscribes a client from all channels.


Example:

```python
from hypern.hypern import WebSocketSession
from room import RoomManager
from channel import ChannelManager
from route import WebsocketRoute

# Create managers
room_manager = RoomManager()
channel_manager = ChannelManager()
websocket_route = WebsocketRoute()

# Define WebSocket route
@websocket_route.on("/ws")
async def websocket_handler(session: WebSocketSession):
    # Handle WebSocket connection
    pass
```

This example demonstrates how to set up a WebSocket route and handle WebSocket connections using the provided components.

Example `room` and `channel`

```python
from hypern.ws import WebsocketRoute, WebSocketSession
from hypern.ws.room import RoomManager
from hypern.ws.channel import ChannelManager

# Initialize managers
room_manager = RoomManager()
channel_manager = ChannelManager()

ws = WebsocketRoute()

# Create a chat channel
chat_channel = channel_manager.create_channel("chat")

@chat_channel.on("message")
async def handle_chat_message(session: WebSocketSession, data: dict):
    """Handle chat messages"""
    await chat_channel.publish("message", {
        "user": data.get("user"),
        "message": data.get("message")
    }, publisher=session)

@ws.on("/ws")
def handle_websocket(session: WebSocketSession, message: str):

    message = orjson.loads(message)
    
    """Handle WebSocket messages"""
    action = message.get("action")
    
    if action == "join_room":
        room_name = message.get("room")
        room_manager.join_room(session, room_name)
        session.send(orjson.dumps({"status": "joined", "room": room_name}))
    
    elif action == "leave_room":
        room_name = message.get("room")
        room_manager.leave_room(session, room_name)
        session.send({"status": "left", "room": room_name})
    
    elif action == "subscribe":
        channel_name = message.get("channel")
        channel_manager.subscribe(session, channel_name)
        session.send({"status": "subscribed", "channel": channel_name})
    
    elif action == "unsubscribe":
        channel_name = message.get("channel")
        channel_manager.unsubscribe(session, channel_name)
        session.send({"status": "unsubscribed", "channel": channel_name})
    
    elif action == "chat":
        chat_channel.handle_event("message", session, {
            "user": message.get("user"),
            "message": message.get("message")
        })
        session.send({"status": "message_sent"})

@ws.on_disconnect
async def handle_disconnect(session: WebSocketSession):
    """Clean up when a client disconnects"""
    room_manager.leave_all_rooms(session)
    channel_manager.unsubscribe_all(session)
```

```js
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5005/ws');

// Join a room
ws.send(JSON.stringify({
    action: 'join_room',
    room: 'general'
}));

// Subscribe to chat channel
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'chat'
}));

// Send a chat message
ws.send(JSON.stringify({
    action: 'chat',
    user: 'John',
    message: 'Hello everyone!'
}));

// Handle incoming messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```


### HeartbeatManager

The `HeartbeatManager` class manages the heartbeat mechanism for WebSocket sessions to ensure they are alive and responsive.

#### Methods

- `start_heartbeat(self, session: WebSocketSession)`: Starts heartbeat monitoring for a session.
- `stop_heartbeat(self, session: WebSocketSession)`: Stops heartbeat monitoring for a session.
- `handle_pong(self, session: WebSocketSession)`: Handles pong responses from the client.

#### Example

```python
from hypern import Hypern
from hypern.ws import WebsocketRoute, WebSocketSession
from hypern.ws.heartbeat import HeartbeatManager, HeartbeatConfig
from hypern.routing import Route, HTTPEndpoint

# Initialize WebSocket route
ws = WebsocketRoute()

# Create heartbeat manager with configuration
heartbeat_manager = HeartbeatManager(HeartbeatConfig(
    ping_interval=30.0,    # Send ping every 30 seconds
    ping_timeout=10.0,     # Wait 10 seconds for pong
    max_missed_pings=2     # Disconnect after 2 missed pings
))

@ws.on("/ws")
async def websocket_handler(session: WebSocketSession):
    """WebSocket connection handler"""
    # Start heartbeat monitoring for this session
    await heartbeat_manager.start_heartbeat(session)
    
    try:
        async for message in session:
            if message.type == "pong":
                await heartbeat_manager.handle_pong(session)
            else:
                # Handle your custom messages here
                try:
                    data = message.json()
                    response = await process_message(data)
                    await session.send(response)
                except Exception as e:
                    await session.send({"error": str(e)})
    finally:
        await heartbeat_manager.stop_heartbeat(session)

@ws.on_disconnect
async def handle_disconnect(session: WebSocketSession):
    """Handle WebSocket disconnection"""
    await heartbeat_manager.stop_heartbeat(session)

async def process_message(data: dict) -> dict:
    """Process incoming WebSocket messages"""
    action = data.get("action")
    if action == "ping":
        return {"action": "pong", "timestamp": time.time()}
    # Add more message handlers here
    return {"action": "unknown"}

# Create regular HTTP endpoint
class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):
        return {"status": "ok", "message": "Server is running"}

# Define routes
routes = [
    Route("/", HomeEndpoint)
]

# Create Hypern application
app = Hypern(
    routes=routes,
    title="WebSocket Demo",
    version="1.0.0"
)

# Add WebSocket routes
app.add_websocket(ws)

if __name__ == "__main__":
    # Start the server
    app.start()
```

This example demonstrates how to integrate the `HeartbeatManager` into a WebSocket route to monitor the connection's health.