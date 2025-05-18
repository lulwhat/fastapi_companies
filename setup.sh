if [ ! -f .env ]; then
  echo ".env not found. Creating from .env.example"
  cp .env.example .env
fi

docker-compose up --build -d