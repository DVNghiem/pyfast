import asyncio
import os
import signal
import sys
from typing import Any, Dict, List

from multiprocess import Process
from watchdog.observers import Observer

from .hypern import FunctionInfo, Router, Server, SocketHeld
from .logging import logger
from .reload import EventHandler


def run_processes(
    host: str,
    port: int,
    workers: int,
    processes: int,
    max_blocking_threads: int,
    router: Router,
    injectables: Dict[str, Any],
    before_request: List[FunctionInfo],
    after_request: List[FunctionInfo],
    response_headers: Dict[str, str],
    reload: bool = True,
) -> List[Process]:
    socket = SocketHeld(host, port)

    process_pool = init_processpool(router, socket, workers, processes, max_blocking_threads, injectables, before_request, after_request, response_headers)

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
    router: Router,
    socket: SocketHeld,
    workers: int,
    processes: int,
    max_blocking_threads: int,
    injectables: Dict[str, Any],
    before_request: List[FunctionInfo],
    after_request: List[FunctionInfo],
    response_headers: Dict[str, str],
) -> List[Process]:
    process_pool = []

    for _ in range(processes):
        copied_socket = socket.try_clone()
        process = Process(
            target=spawn_process,
            args=(router, copied_socket, workers, max_blocking_threads, injectables, before_request, after_request, response_headers),
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
    router: Router,
    socket: SocketHeld,
    workers: int,
    max_blocking_threads: int,
    injectables: Dict[str, Any],
    before_request: List[FunctionInfo],
    after_request: List[FunctionInfo],
    response_headers: Dict[str, str],
):
    loop = initialize_event_loop()

    server = Server()
    server.set_router(router=router)
    server.set_injected(injected=injectables)
    server.set_before_hooks(hooks=before_request)
    server.set_after_hooks(hooks=after_request)
    server.set_response_headers(headers=response_headers)

    try:
        server.start(socket, workers, max_blocking_threads)
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
