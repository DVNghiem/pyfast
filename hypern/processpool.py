import asyncio
from multiprocess import Process
import signal
import sys
from typing import List, Dict, Any
from .hypern import SocketHeld, Server, Router
from .logging import logger


def run_processes(host: str, port: int, workers: int, processes: int, router: Router, injectables: Dict[str, Any]) -> List[Process]:
    socket = SocketHeld(host, port)

    process_pool = init_processpool(router, socket, workers, processes, injectables)

    def terminating_signal_handler(_sig, _frame):
        logger.info("Terminating server!!", bold=True)
        for process in process_pool:
            process.kill()

    signal.signal(signal.SIGINT, terminating_signal_handler)
    signal.signal(signal.SIGTERM, terminating_signal_handler)

    logger.info("Press Ctrl + C to stop \n")
    for process in process_pool:
        process.join()

    return process_pool


def init_processpool(router: Router, socket: SocketHeld, workers: int, processes: int, injectables: Dict[str, Any]) -> List[Process]:
    process_pool = []
    if sys.platform.startswith("win32") or processes == 1:
        spawn_process(router, socket, workers, 1, injectables)

        return process_pool

    for _ in range(processes):
        copied_socket = socket.try_clone()
        process = Process(
            target=spawn_process,
            args=(router, copied_socket, workers, 1, injectables),
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


def spawn_process(router: Router, socket: SocketHeld, workers: int, processes: int, injectables: Dict[str, Any]):
    loop = initialize_event_loop()

    server = Server()
    server.set_router(router=router)
    server.set_injected(injected=injectables)

    try:
        server.start(socket, workers, processes)
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
