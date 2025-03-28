#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres is not started yet..."

    # check host and port access
    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 1
    done

    echo "PostgreSQL is started"
fi

exec "$@"