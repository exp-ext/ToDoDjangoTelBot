#!/bin/bash

# Проверка, запущен ли docker compose


if [ $(docker compose ps -q | wc -l) -gt 0 ]; then
    echo "Дампим статистику..."
    docker compose exec web python manage.py dump_redis
    echo "Дампим базу данных..."
    docker compose exec web python3 manage.py dumpdata --exclude posts.postcontents --exclude auth.permission --exclude contenttypes --exclude defender.accessattempt > db.json
    echo "Docker Compose уже работает. Перезапускаю..."
    docker compose down && docker compose up --build -d
else
    echo "Docker Compose не работает. Запускаю..."
    docker compose up --build -d
fi
