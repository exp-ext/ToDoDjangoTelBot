<h1 align="center">ToDo Telegram bot</h1>

![статус](https://github.com/exp-ext/ToDoDjangoTelBot/actions/workflows/main.yml/badge.svg?event=push)

<p align="center"><img src="https://github.com/exp-ext/ToDoDjangoTelBot/blob/master/todo/static/git/background.jpg" width="700" /></p>

<hr />
<div><h3>The project is a task and note manager integrated with Telegram. Its goals include:</h3>
<p>&nbsp; &nbsp;This application is a system of reminders and notes integrated into the Telegram bot.<br />Reminders can be created both in chat, using dialog interaction with the bot, and on the website, where it is possible to add a picture to the reminder. A handy text editor is integrated into the notes form, allowing<br />create beautiful posts in your public spaces.<br />&nbsp; &nbsp; Additionally the program works with API from OpenAI (Davinchi 3, Dall-E, Whisper). Answer generation includes previous dialogs for the last 10 minutes, which gives you an opportunity to refine your request without creating a new one. <br />&nbsp; &nbsp; The bot can tell jokes, give the current 4-day weather forecast for your location, and translate messages into your opponent's native language to help communicate with someone who doesn't know your language. Makes an audio transcription of your Telegram chat messages.</p>
<hr />

<h3>Deployment and project launch</h3>
<div class="w-[30px] flex flex-col relative items-end">To deploy the project, you need to clone it to your server.&nbsp;</div>

```
$ git clone https://github.com/exp-ext/ToDoDjangoTelBot.git
```

<div class="w-[30px] flex flex-col relative items-end">&nbsp;</div>
<div class="w-[30px] flex flex-col relative items-end">Add a .env file with tokens, passwords, and settings. The template for filling the file is in /infra_todo/.env.example;</div>

<div class="w-[30px] flex flex-col relative items-end">Go to the /infra_todo folder and run the project with Docker by running the following command:</div>

```
$ docker-compose up -d --build
```
<hr />
<p><em>Note: Before running the above command, make sure that you have Docker and Docker Compose installed on your server. You may also need to adjust the Docker Compose file to fit your specific configuration needs.</em></p>
<hr />
<h3>Project author:</h3>
<p>Borokin Andrey</p>

GITHUB: [exp-ext](https://github.com/exp-ext)

[![Join Telegram](https://img.shields.io/badge/My%20Telegram-Join-blue)](https://t.me/Borokin)
