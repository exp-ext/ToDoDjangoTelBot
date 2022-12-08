release: python manage.py migrate --noinput
web: gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker todo.asgi:application
worker: celery -A todo worker -P prefork --loglevel=INFO 
beat: celery -A todo beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler