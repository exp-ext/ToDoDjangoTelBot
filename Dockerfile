# Use the official lightweight Python image as the base image
FROM python:3.11.2-slim-bullseye

# Set working directory
WORKDIR /app

# Install dependencies and clean up
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y \
        gcc \
        libpq-dev \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install pipenv and psycopg2-binary
RUN pip install --upgrade pip && \
    pip install \
    pipenv psycopg2-binary --no-binary psycopg2-binary

# install dependencies
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip/ \
    pip install -r requirements.txt

# Copy the project to the container
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

# Create the appropriate directories
RUN mkdir -p /app/web/static /app/web/media

# Set the entrypoint and make it executable
RUN chmod +x /app/conf_sh/web_entrypoint.sh

RUN python todo/manage.py collectstatic --no-input

# Create an unprivileged user to run the application
RUN addgroup --system app && \
    adduser --system --ingroup app app

USER app
