import sys
import time
import subprocess
from watchdog.events import FileSystemEventHandler
import signal
import os

from .logging import logger


class EventHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, directory_path: str) -> None:
        self.file_path = file_path
        self.directory_path = directory_path
        self.process = None
        self.last_reload = time.time()

    def reload(self):
        # Kill all existing processes with the same command
        current_cmd = [sys.executable, *sys.argv]

        try:
            # Find and kill existing processes
            for proc in subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE).communicate()[0].decode().splitlines():
                if all(str(arg) in proc for arg in current_cmd):
                    pid = int(proc.split()[1])
                    try:
                        os.kill(pid, signal.SIGKILL)  # NOSONAR
                        logger.debug(f"Killed process with PID {pid}")
                    except ProcessLookupError:
                        pass

            # Start new process
            self.process = subprocess.Popen(current_cmd)
            self.last_reload = time.time()
            logger.debug("Server reloaded successfully")

        except Exception as e:
            logger.error(f"Reload failed: {e}")

    def on_modified(self, event) -> None:
        if time.time() - self.last_reload < 0.5:
            return

        time.sleep(0.2)  # Ensure file is written
        self.reload()
