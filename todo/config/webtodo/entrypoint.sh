#!/bin/sh

# url="http://localhost:9000/data/"

# while true; do
#   response=$(curl --output /dev/null --head --fail "$url" 2>&1)
#   exit_code=$?
  
#   if [[ $exit_code -eq 7 ]]; then
#     echo "Ошибка подключения. Ожидание 10 секунд..."
#     sleep 10
#   else
#     break
#   fi
# done

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
