#!/bin/sh

cd /app/

echo "Начало collectstatic..."

until python3 manage.py collectstatic --no-input;
do
    echo "Ожидание collectstatic..."
    sleep 5
done

until python3 manage.py migrate;
do
    echo "Ожидание готовности базы данных... No migrate..."
    sleep 5
done

gunicorn -c config/gunicorn/dev.py
