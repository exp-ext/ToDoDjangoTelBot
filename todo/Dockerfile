FROM python:3.11.0

ENV PYTHONUNBUFFERED=1

RUN mkdir /app

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/
