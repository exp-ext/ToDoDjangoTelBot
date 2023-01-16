import os

import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')


def get_answer_davinci(update: Update, context: CallbackContext):
    chat = update.effective_chat
    prompt = update.message.text
    model_engine = 'text-davinci-003'

    try:
        answer = openai.Completion.create(
            engine=model_engine,
            prompt=prompt[prompt.index('\n')+1::],
            max_tokens=1024,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        context.bot.send_message(
            chat.id,
            answer.choices[0].text,
            parse_mode='Markdown'
        )
    except Exception as error:
        context.bot.send_message(225429268, error)
        raise KeyError(error)
    return 'Done'
