import asyncio
from dataclasses import dataclass
from time import time
from typing import Dict

from hypern.hypern import WebSocketSession


@dataclass
class HeartbeatConfig:
    ping_interval: float = 30.0  # Send ping every 30 seconds
    ping_timeout: float = 10.0  # Wait 10 seconds for pong response
    max_missed_pings: int = 2  # Disconnect after 2 missed pings


class HeartbeatManager:
    def __init__(self, config: HeartbeatConfig = None):
        self.config = config or HeartbeatConfig()
        self.active_sessions: Dict[WebSocketSession, float] = {}
        self.ping_tasks: Dict[WebSocketSession, asyncio.Task] = {}
        self.missed_pings: Dict[WebSocketSession, int] = {}

    async def start_heartbeat(self, session: WebSocketSession):
        """Start heartbeat monitoring for a session"""
        self.active_sessions[session] = time()
        self.missed_pings[session] = 0
        self.ping_tasks[session] = asyncio.create_task(self._heartbeat_loop(session))

    async def stop_heartbeat(self, session: WebSocketSession):
        """Stop heartbeat monitoring for a session"""
        if session in self.ping_tasks:
            self.ping_tasks[session].cancel()
            del self.ping_tasks[session]
            self.active_sessions.pop(session, None)
            self.missed_pings.pop(session, None)

    async def handle_pong(self, session: WebSocketSession):
        """Handle pong response from client"""
        if session in self.active_sessions:
            self.active_sessions[session] = time()
            self.missed_pings[session] = 0

    async def _heartbeat_loop(self, session: WebSocketSession):
        """Main heartbeat loop for a session"""
        try:
            while True:
                await asyncio.sleep(self.config.ping_interval)

                if session not in self.active_sessions:
                    break

                # Send ping frame
                try:
                    await session.ping()
                    last_pong = self.active_sessions[session]

                    # Wait for pong timeout
                    await asyncio.sleep(self.config.ping_timeout)

                    # Check if we received a pong
                    if self.active_sessions[session] == last_pong:
                        self.missed_pings[session] += 1

                        # Check if we exceeded max missed pings
                        if self.missed_pings[session] >= self.config.max_missed_pings:
                            await session.close(1001, "Connection timeout")
                            break

                except Exception as e:
                    await session.close(1001, f"Heartbeat failed: {str(e)}")
                    break

        finally:
            await self.stop_heartbeat(session)
