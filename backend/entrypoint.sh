#!/bin/sh

alembic upgrade head
python ./load_initial_data.py

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir ./app