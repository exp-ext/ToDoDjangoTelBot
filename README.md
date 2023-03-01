<h1 align="center">Django ToDo Telegram bot</h1>
<p align="center"><img src="https://github.com/exp-ext/GitProjects/blob/main/pythons.png" width="700" /></p>
<div><strong>The project is a task and note manager integrated with Telegram. Its goals include:</strong></div>
<p>&nbsp; &nbsp; This application is a system of reminders and notes integrated into the Telegram bot. <br />Reminders can be created both in chat, using dialog interaction with the bot, and on the website, where it is possible to add a picture to the reminder. A handy text editor is integrated into the memo form, allowing<br /> create beautiful posts.<br />&nbsp; &nbsp; In addition the program works with API from OpenAI (Davinchi 3, Dall-E, Whisper). Answer generation includes previous dialogs for the last 5 minutes which gives you an opportunity to refine your request without creating a new one. Bot can parse sites with jokes, give the current weather forecast for 4 days by your location and also translate messages into your opponent's native language to help chat with a person who doesn't know your language. Makes audio transcription of your Telegram chat messages.</p>
<div class="w-[30px] flex flex-col relative items-end">&nbsp;</div>
<div class="w-[30px] flex flex-col relative items-end">To deploy the project, you need to clone it to your server.&nbsp;</div>
<p><code class="!whitespace-pre hljs language-css"><code class="!whitespace-pre hljs language-css"></code></code></p>
<div class="w-[30px] flex flex-col relative items-end">https://github.com/exp-ext/ToDoDjangoTelBot.git</div>
<p><code class="!whitespace-pre hljs language-css">
  </code></p>
<div class="w-[30px] flex flex-col relative items-end">&nbsp;</div>
<div class="w-[30px] flex flex-col relative items-end">Add a .env file with tokens, passwords, and settings. Launch the project using Docker by running the following command:</div>
<div class="relative flex w-[calc(100%-50px)] flex-col gap-1 md:gap-3 lg:w-[calc(100%-115px)]">
<div class="flex flex-grow flex-col gap-3">
<div class="min-h-[20px] flex flex-col items-start gap-4 whitespace-pre-wrap">
<div class="markdown prose w-full break-words dark:prose-invert dark">
<div class="bg-black mb-4 rounded-md">
<div class="flex items-center relative text-gray-200 bg-gray-800 px-4 py-2 text-xs font-sans">&nbsp;</div>
</div>
</div>
</div>
</div>
</div>
<div class="bg-black mb-4 rounded-md">
<div class="p-4 overflow-y-auto">docker-compose up <span class="hljs-attr">--build</span></div>
</div>
<p><em>Note: Before running the above command, make sure that you have Docker and Docker Compose installed on your server. You may also need to adjust the Docker Compose file to fit your specific configuration needs.</em></p>
<p>&nbsp;</p>
