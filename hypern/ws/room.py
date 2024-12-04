from dataclasses import dataclass, field
from typing import Dict, Set

from hypern.hypern import WebSocketSession


@dataclass
class Room:
    name: str
    clients: Set[WebSocketSession] = field(default_factory=set)

    def broadcast(self, message: str, exclude: WebSocketSession = None):
        """Broadcast message to all clients in the room except excluded one"""
        for client in self.clients:
            if client != exclude:
                client.send(message)

    def add_client(self, client: WebSocketSession):
        """Add a client to the room"""
        self.clients.add(client)

    def remove_client(self, client: WebSocketSession):
        """Remove a client from the room"""
        self.clients.discard(client)

    @property
    def client_count(self) -> int:
        return len(self.clients)


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.client_rooms: Dict[WebSocketSession, Set[str]] = {}

    def create_room(self, room_name: str) -> Room:
        """Create a new room if it doesn't exist"""
        if room_name not in self.rooms:
            self.rooms[room_name] = Room(room_name)
        return self.rooms[room_name]

    def get_room(self, room_name: str) -> Room:
        """Get a room by name"""
        return self.rooms.get(room_name)

    def join_room(self, client: WebSocketSession, room_name: str):
        """Add a client to a room"""
        room = self.create_room(room_name)
        room.add_client(client)

        if client not in self.client_rooms:
            self.client_rooms[client] = set()
        self.client_rooms[client].add(room_name)

        room.broadcast(f"Client joined room: {room_name}", exclude=client)

    def leave_room(self, client: WebSocketSession, room_name: str):
        """Remove a client from a room"""
        room = self.get_room(room_name)
        if room:
            room.remove_client(client)
            if client in self.client_rooms:
                self.client_rooms[client].discard(room_name)

            room.broadcast(f"Client left room: {room_name}", exclude=client)

            if room.client_count == 0:
                del self.rooms[room_name]

    def leave_all_rooms(self, client: WebSocketSession):
        """Remove a client from all rooms"""
        if client in self.client_rooms:
            rooms = self.client_rooms[client].copy()
            for room_name in rooms:
                self.leave_room(client, room_name)
            del self.client_rooms[client]
