#!/bin/sh

until cd /app/todo/
do
    echo "Waiting for server volume..."
done

until python manage.py migrate
do
    echo "Waiting for db to be ready... No migrate..."
    sleep 2
done

until python manage.py set_ip_by_host
do
    echo "Waiting seting IP..."
    sleep 2
done

gunicorn -c config/gunicorn/dev.py
