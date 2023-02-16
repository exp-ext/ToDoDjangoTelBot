#! /bin/bash

PROJECT_DIR=~/ToDoDjangoTelBot

DATE=$(date '+%Y-%m-%d %H:%M:%S')

cd $PROJECT_DIR/

status ()
{
	docker ps | grep docker | grep -v grep
}

damp_db()
{
	docker-compose exec web python3 todo/manage.py dumpdata --exclude auth.permission --exclude contenttypes > db.json >> $PROJECT_DIR/sh_logs/docker-application.log 2>&1
}

send_mail()
{
	echo "DB from YourToDo" | mutt -a "./db.json" -s "DB dump from $DATE" -- yourtodo@yandex.ru
}

delete()
{
	rm ./db.json && docker-compose exec web rm /app/db.json
}

if status	
	damp_db
	sleep 180
	send_mail
	sleep 120
	delete
fi

