# pull official base image
FROM python:3.11.0

RUN apt-get update && apt-get upgrade -y

# install psycopg dependencies
RUN apt-get install -y \
        python3-dev \
        libpq-dev \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# collectstatic needs the secret key to be set. We store that in this environment variable.
# Set this value in this project's .env file
RUN pip install pipenv
ARG DJANGO_SECRET_KEY

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# create the appropriate directories
ENV APP_HOME=/app
RUN mkdir -p $APP_HOME
RUN mkdir -p $APP_HOME/web/static
RUN mkdir -p $APP_HOME/web/media
WORKDIR $APP_HOME

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
COPY requirements.txt $APP_HOME
RUN pip install -r requirements.txt

# copy project
COPY . $APP_HOME

RUN chmod +x $APP_HOME/entrypoint.sh

RUN python todo/manage.py collectstatic --no-input
