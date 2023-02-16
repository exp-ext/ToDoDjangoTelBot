#! /bin/bash

PROJECT_DIR=~/ToDoDjangoTelBot

cd $PROJECT_DIR/

status ()
{
	docker ps | grep docker | grep -v grep
}

start()
{
	docker-compose up -d --build >> $PROJECT_DIR/restart/docker-application.log 2>&1
}

stop()
{
	docker-compose down &
}

remove()
{
	docker volume rm tododjangotelbot_static_volume	&
}

if status
then
	stop
	sleep 30
	remove
	sleep 5	
	start
else		
	start
fi

