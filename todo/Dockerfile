# Use the official lightweight Python image as the base image
FROM python:3.11.2-slim-bullseye

# Set working directory
WORKDIR /app

# Install dependencies for psycopg2-binary and clean up
RUN --mount=type=cache,target=/var/cache/apt/archives/ \
    apt-get update && apt-get install --no-install-recommends --no-install-suggests -y \
        gcc \
        libpq-dev \
        python3-dev \
        pipenv \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# install dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip/ \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install psycopg2-binary --no-binary psycopg2-binary

# Copy the project to the container
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SECRET_KEY=DJANGO_SECRET_KEY

RUN python3 manage.py collectstatic --no-input

# Create an unprivileged user to run the application
RUN addgroup --system apps-group && \
    adduser --system --ingroup apps-group app-user

# Set permissions on the application directory
RUN chown -R app-user:apps-group /app/ && \
    chmod -R 770 /app/ && \
    chmod -R 777 /app/logs/

# Switch to the non-root user
USER app-user
