#!/bin/bash

# NETWORK_NAME="minionetwork"

# # # Проверяем существование сети
# if [ -z "$(docker network ls -q -f name=$NETWORK_NAME)" ]; then
#   echo "Network $NETWORK_NAME не найдена. Создаю..."
#   docker network create $NETWORK_NAME
# fi

# # Проверка наличия volume media_volume
# if ! docker volume inspect media_volume > /dev/null 2>&1; then
#     echo "Volume 'media_volume' не найден. Создаю..."
#     docker volume create media_volume
# fi

# # Проверка наличия volume static_volume
# if ! docker volume inspect static_volume > /dev/null 2>&1; then
#     echo "Volume 'static_volume' не найден. Создаю..."
#     docker volume create --driver local --opt type=tmpfs --opt device=tmpfs --opt o=size=1g static_volume
# fi

# Проверка, запущен ли docker compose

if [ $(docker compose ps -q | wc -l) -gt 0 ]; then
    echo "Docker Compose уже работает. Перезапускаю..."
    docker compose down && docker compose up --build -d
else
    echo "Docker Compose не работает. Запускаю..."
    docker compose up --build -d
fi

sleep 10
docker compose logs nginx