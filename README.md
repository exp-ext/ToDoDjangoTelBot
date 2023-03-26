<h1 align="center">Django ToDo Telegram bot</h1>
<p align="center"><img src="https://github.com/exp-ext/GitProjects/blob/main/pythons.png" width="700" /></p>
<div><h3><em>The project is a task and note manager integrated with Telegram. Its goals include:</em></h3>
<p><em>&nbsp; &nbsp; This application is a system of reminders and notes integrated into the Telegram bot. </em><br /><em>Reminders can be created both in chat, using dialog interaction with the bot, and on the website, where it is possible to add a picture to the reminder. A handy text editor is integrated into the memo form, allowing</em><br /><em> create beautiful posts.</em><br /><em>&nbsp; &nbsp; In addition the program works with API from OpenAI (Davinchi 3, Dall-E, Whisper). Answer generation includes previous dialogs for the last 5 minutes which gives you an opportunity to refine your request without creating a new one. Bot can parse sites with jokes, give the current weather forecast for 4 days by your location and also translate messages into your opponent's native language to help chat with a person who doesn't know your language. Makes audio transcription of your Telegram chat messages.</em></p>
<div class="w-[30px] flex flex-col relative items-end">&nbsp;</div>
<div class="w-[30px] flex flex-col relative items-end">To deploy the project, you need to clone it to your server.&nbsp;</div>

```
$ git clone https://github.com/exp-ext/ToDoDjangoTelBot.git
```

<div class="w-[30px] flex flex-col relative items-end">&nbsp;</div>
<div class="w-[30px] flex flex-col relative items-end">Add a .env file with tokens, passwords, and settings.</div>

```
# DJANGO
DEBUG=0
DOMAIN=...
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=localhost ...

# TELEGRAM BOT
TOKEN=...
# Telegram
ADMIN_ID=...
# https://home.openweathermap.org/api_keys
OW_API_ID=...
# https://yandex.com/dev/maps/geocoder/
YANDEX_GEO_API=...
# email
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
# redis
REDIS_URL=redis://redis:6379
# POSTGRESSQL
POSTGRES_ENGINE=django.db.backends.postgresql
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=db
POSTGRES_PORT=5432
# DNS
LOGIN_DNS_API=...
PASSWORD_DNS_API=...
HOST_FOR_DNS=...
# ChatGPT API
CHAT_GP_TOKEN=...
# Translaters
X_RAPID_API_KEY=...
# Monitoring
SENTRY_KEY=...
```
<div class="w-[30px] flex flex-col relative items-end">Launch the project using Docker by running the following command:</div>

```
$ docker-compose up 
```

<p><em>Note: Before running the above command, make sure that you have Docker and Docker Compose installed on your server. You may also need to adjust the Docker Compose file to fit your specific configuration needs.</em></p>
<p>&nbsp;</p>
