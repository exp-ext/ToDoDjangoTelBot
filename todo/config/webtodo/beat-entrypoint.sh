#!/bin/sh

url="http://localhost:8000/health/live/"

while true; do
  response=$(curl --output /dev/null --head --fail "$url" 2>&1)
  exit_code=$?
  
  if [[ $exit_code -eq 7 ]]; then
    echo "Ожидание запуска основного приложения. Повторная проверка через 10 секунд..."
    sleep 10
  else
    break
  fi
done


celery -A todo beat -l info --scheduler django_celery_beat.schedulers.DatabaseScheduler
