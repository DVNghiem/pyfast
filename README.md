# VA Portal API
```
├── conf
│   ├── gunicorn.py
│   └── supervisor
│       └── worker.conf # config suppervisor
├── docker-compose.yml
├── Dockerfile
├── ex.env # example for .env file
├── main.py
├── Makefile
├── MANIFEST.in
├── pyproject.toml
├── README.md
├── requirements.txt
├── setup.py
├── src
│   ├── apis # all API write here
│   │   ├── health_check.py
│   │   ├── __init__.py # routing api write here
│   ├── application.py
│   ├── config.py # Config file auto read value from .env
│   ├── connect.py # Connect database, redis, ...
│   ├── helper
│   │   ├── account.py # Logic in API
│   │   ├── __init__.py
│   ├── __init__.py
│   ├── lib
│   │   ├── authentication.py
│   │   ├── ...
│   ├── models # Define collection/table of database
│   │   ├── __init__.py
│   ├── schema # Define schema validate input and output api
│   │   ├── account.py
│   │   ├── __init__.py
│   ├── tasks # Process task for worker celery
│   │   └── __init__.py # Import all task into __init__.py
│   └── worker.py
└── worker.py
```

## Run
- Before run: you must create python environment: `python3 -m venv venv`
- Then, you active env: `source ./venv/bin/active`
- Install dependency package: `pip3 install -r requirements.txt --no-cache`
- Finally, you can run: `python3 main.py`

## Migrate database
- Create migrate file: `alembic revision --autogenerate -m "<message>"`
- Update to database: `alembic upgrade head`
