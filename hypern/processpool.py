import asyncio
import os
import signal
import sys
from typing import List

from multiprocess import Process
from watchdog.observers import Observer

from .hypern import Server, SocketHeld
from .logging import logger
from .reload import EventHandler


def run_processes(
    server: Server,
    host: str,
    port: int,
    workers: int,
    processes: int,
    max_blocking_threads: int,
    reload: bool = True,
) -> List[Process]:
    socket = SocketHeld(host, port)

    process_pool = init_processpool(
        server,
        socket,
        workers,
        processes,
        max_blocking_threads,
    )

    def terminating_signal_handler(_sig, _frame):
        logger.info("Terminating server!!")
        for process in process_pool:
            process.kill()

    signal.signal(signal.SIGINT, terminating_signal_handler)
    signal.signal(signal.SIGTERM, terminating_signal_handler)

    if reload:
        # Set up file system watcher for auto-reload
        watch_dirs = [os.getcwd()]
        observer = Observer()
        reload_handler = EventHandler(file_path=sys.argv[0], directory_path=os.getcwd())

        for directory in watch_dirs:
            observer.schedule(reload_handler, directory, recursive=True)

        observer.start()

    logger.info(f"Server started at http://{host}:{port}")
    logger.info("Press Ctrl + C to stop")

    try:
        for process in process_pool:
            logger.debug(f"Process {process.pid} started")
            process.join()
    except KeyboardInterrupt:
        pass
    finally:
        if reload:
            observer.stop()
            observer.join()

    return process_pool


def init_processpool(
    server: Server,
    socket: SocketHeld,
    workers: int,
    processes: int,
    max_blocking_threads: int,
) -> List[Process]:
    process_pool = []

    for _ in range(processes):
        copied_socket = socket.try_clone()
        process = Process(
            target=spawn_process,
            args=(
                server,
                copied_socket,
                workers,
                max_blocking_threads,
            ),
        )
        process.start()
        process_pool.append(process)

    return process_pool


def initialize_event_loop():
    if sys.platform.startswith("win32") or sys.platform.startswith("linux-cross"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    else:
        import uvloop

        uvloop.install()
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def spawn_process(
    server: Server,
    socket: SocketHeld,
    workers: int,
    max_blocking_threads: int,
):
    loop = initialize_event_loop()

    try:
        server.start(socket, workers, max_blocking_threads)
    except KeyboardInterrupt:
        loop.close()
