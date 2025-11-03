#!/bin/sh

if [ "$SQL_DB" = "het" ]
then
    echo "Waiting for postgres..."
    echo $SQL_HOST
    echo $SQL_PORT

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

alembic upgrade head

exec "$@"
