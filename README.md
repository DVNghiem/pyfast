
## Run
- Before run: you must create python environment: `python3 -m venv venv`
- Then, you active env: `source ./venv/bin/active`
- Install dependency package: `pip3 install -r requirements.txt --no-cache`
- Develop: `python3 -m robyn main.py --dev --log-level DEBUG`
- Deploy scale: `python3 main.py --workers=N --precess=M --log-level DEBUG`

## Migrate database
- Create migrate file: `alembic revision --autogenerate -m "<message>"`
- Update to database: `alembic upgrade head`
