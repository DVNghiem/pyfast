import signal
import sys
import time
import os
import subprocess
from watchdog.events import FileSystemEventHandler

from .logging import logger


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, directory_path: str) -> None:
        self.file_path = file_path
        self.directory_path = directory_path
        self.process = None  # Keep track of the subprocess
        self.last_reload = time.time()  # Keep track of the last reload. EventHandler is initialized with the process.

    def stop_server(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGTERM)  # Stop the subprocess using os.kill()

    def reload(self):
        self.stop_server()
        logger.debug("Reloading the server")
        prev_process = self.process
        if prev_process:
            prev_process.kill()

        self.process = subprocess.Popen(
            [sys.executable, *sys.argv],
        )

        self.last_reload = time.time()

    def on_modified(self, event) -> None:
        """
        This function is a callback that will start a new server on every even change

        :param event FSEvent: a data structure with info about the events
        """

        # Avoid reloading multiple times when watchdog detects multiple events
        if time.time() - self.last_reload < 0.5:
            return

        time.sleep(0.2)  # Wait for the file to be fully written
        self.reload()
