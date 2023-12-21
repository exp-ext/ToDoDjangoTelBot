#!/bin/bash

# Проверка наличия volume media_volume
if ! docker volume inspect media_volume > /dev/null 2>&1; then
    echo "Volume 'media_volume' не найден. Создаю..."
    docker volume create --driver local --opt type=tmpfs --opt device=tmpfs --opt o=size=1g media_volume
fi

# Проверка наличия volume static_volume
if ! docker volume inspect static_volume > /dev/null 2>&1; then
    echo "Volume 'static_volume' не найден. Создаю..."
    docker volume create --driver local --opt type=tmpfs --opt device=tmpfs --opt o=size=1g static_volume
fi

# Проверка, запущен ли docker compose

if [ $(docker compose ps -q | wc -l) -gt 0 ]; then
    echo "Docker Compose уже работает. Перезапускаю..."
    docker compose down && docker compose up --build -d
else
    echo "Docker Compose не работает. Запускаю..."
    docker compose -p up --build -d
fi