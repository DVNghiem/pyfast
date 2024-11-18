import asyncio
from multiprocess import Process
import signal
import sys
from typing import List
from .hypern import SocketHeld, Server, Router
from .logging import logger


def run_processes(
    host: str,
    port: int,
    router: Router,
    workers: int,
    processes: int,
) -> List[Process]:
    socket = SocketHeld(host, port)

    process_pool = init_processpool(
        router,
        socket,
        workers,
        processes,
    )

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


def init_processpool(
    router: Router,
    socket: SocketHeld,
    workers: int,
    processes: int,
) -> List[Process]:
    process_pool = []
    if sys.platform.startswith("win32") or processes == 1:
        spawn_process(router, socket, workers, 1)

        return process_pool

    for _ in range(processes):
        copied_socket = socket.try_clone()
        process = Process(
            target=spawn_process,
            args=(router, copied_socket, workers, 1),
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
        # uv loop doesn't support windows or arm machines at the moment
        # but uv loop is much faster than native asyncio
        import uvloop

        uvloop.install()
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def spawn_process(router: Router, socket: SocketHeld, workers: int, processes: int):
    """
    This function is called by the main process handler to create a server runtime.
    This functions allows one runtime per process.

    :param directories List: the list of all the directories and related data
    :param headers tuple: All the global headers in a tuple
    :param routes Tuple[Route]: The routes tuple, containing the description about every route.
    :param middlewares Tuple[Route]: The middleware routes tuple, containing the description about every route.
    :param web_sockets list: This is a list of all the web socket routes
    :param event_handlers Dict: This is an event dict that contains the event handlers
    :param socket SocketHeld: This is the main tcp socket, which is being shared across multiple processes.
    :param process_name string: This is the name given to the process to identify the process
    :param workers int: This is the name given to the process to identify the process
    """

    loop = initialize_event_loop()

    server = Server()
    server.set_router(router=router)

    try:
        server.start(socket, workers, processes)
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
