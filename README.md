
# Pyfast

Pyfast: A Versatile Python and Rust Framework

Pyfast is a flexible, open-source framework built on the [Robyn](https://github.com/sparckles/Robyn/), designed to jumpstart your high-performance web development endeavors. By providing a pre-configured structure and essential components, Pyfast empowers you to rapidly develop custom web applications that leverage the combined power of Python and Rust.

With Pyfast, you can seamlessly integrate asynchronous features and build scalable solutions for RESTful APIs and dynamic web applications. Its intuitive design and robust tooling allow developers to focus on creating high-quality code while maximizing performance. Embrace the synergy of Python and Rust to elevate your web development experience.


### 🏁 Get started

### ⚙️ To Develop Locally

- Setup a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```
- Install required packages

```
pip install pre-commit poetry maturin
```
- Install development dependencies
```
poetry install --with dev --with test
```
- Install pre-commit git hooks
```
pre-commit install
```
- Build & install Robyn Rust package
```
maturin develop
```

## 🤔 Usage

### 🏃 Run your code

This using default CLI Robyn, you can see bellow. You will then have access to a server on the `localhost:5005`,
```python
# main.py
from pyfast import PyFast
from pyfast.routing import Route, HTTPEndpoint

class MyEndpoint(HTTPEndpoint):
    
    async def get(self, global_dependencies):
        return {"data": "Hello World"}

routing = [
    Route("/hello", MyEndpoint)
]

app = PyFast(routing)

if __name__ == "__main__":
    app.start(host='localhost', port=5005)
```

```
$ python3 main.py
```

To see the usage

```
usage: main.py [-h] [--processes PROCESSES] [--workers WORKERS] [--dev] [--log-level LOG_LEVEL]

options:
  -h, --help                show this help message and exit
  --processes PROCESSES     Choose the number of processes. [Default: 1]
  --workers WORKERS         Choose the number of workers. [Default: 1]
  --dev                     Development mode. It restarts the server based on file changes.
  --log-level LOG_LEVEL     Set the log level name
  --create                  Create a new project template.
  --docs                    Open the Robyn documentation.
  --open-browser            Open the browser on successful start.
```

Log level can be `DEBUG`, `INFO`, `WARNING`, or `ERROR`.

You can open swagger UI at path `/docs` 


## 💡 Features

Comming Soon !


## ✨ Special thanks

Special thanks to the [PyO3](https://pyo3.rs/v0.13.2/) community and [Robyn](https://github.com/sparckles/Robyn) for their amazing libraries 💖
