@echo off

if not exist .env (
  echo .env not found. Creating from .env.example
  copy .env.example .env
)

docker-compose up --build -d