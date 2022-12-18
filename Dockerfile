# pull official base image
FROM python:3.11.0

RUN apt-get update -y
RUN apt-get upgrade -y

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
