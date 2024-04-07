import multiprocessing
import os

env = os.getenv("ENV")

if env.lower() != "prod":
    _num_cpu = 2
else:
    _num_cpu = multiprocessing.cpu_count()

backlog = 2048

workers = _num_cpu
threads = 1
worker_class = "uvicorn.workers.UvicornH11Worker"
worker_connections = 1024 * _num_cpu

timeout = 30
keepalive = 2
spew = False
daemon = False

loglevel = "debug"

capture_output = False
preload_app = True
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 8190

max_requests = 3000
max_requests_jitter = 50
