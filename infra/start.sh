#!/bin/bash

# Проверка, запущен ли docker compose

if [ $(docker compose ps -q | wc -l) -gt 0 ]; then
    echo "Docker Compose уже работает. Перезапускаю..."
    docker compose down && docker compose up --build -d
else
    echo "Docker Compose не работает. Запускаю..."
    docker compose up --build -d
fi