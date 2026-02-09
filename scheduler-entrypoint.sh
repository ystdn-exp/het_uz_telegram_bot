#!/bin/sh

set -e

if [ "$SQL_HOST" ] && [ "$SQL_PORT" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

if [ "$REDIS_HOST" ] && [ "$REDIS_PORT" ]
then
    echo "Waiting for redis..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 0.1
    done
    echo "Redis started"
fi

# We do NOT run migrations here to avoid race conditions with the web service
# alembic upgrade head

exec "$@"
