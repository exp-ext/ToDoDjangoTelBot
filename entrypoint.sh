#!/bin/bash

cd todo

python3 manage.py set_webhook

python3 manage.py makemigrations

python3 manage.py migrate

gunicorn -c config/gunicorn/dev.py
