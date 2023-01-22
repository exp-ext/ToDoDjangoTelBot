import os

import requests
from dotenv import load_dotenv

load_dotenv()

TRANSLATOR_USERNAME = os.getenv('TRANSLATOR_USERNAME')
TRANSLATOR_PASSWORD = os.getenv('TRANSLATOR_PASSWORD')


def translate():

    url = 'https://ibmwatsonlanguagetranslatordimasv1.p.rapidapi.com/translate'
    payload = (
        f'username={TRANSLATOR_USERNAME}'
        '&text=Привет! Как ты?'
        '&source=ru'
        '&target=en'
        f'&password={TRANSLATOR_PASSWORD}'
    )
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": "1b78e47ca8msh83f8ddaec5cca20p1c8f1ajsn18e88686aab8",
        "X-RapidAPI-Host": "IBMWatsonLanguageTranslatordimasV1.p.rapidapi.com"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
    except Exception as error:
        raise KeyError(error)

    print(response.text)


def get_models():
    url = "https://ibmwatsonlanguagetranslatordimasv1.p.rapidapi.com/getModels"

    payload = (
        f'username={TRANSLATOR_USERNAME}'
        f'&password={TRANSLATOR_PASSWORD}'
    )
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": "1b78e47ca8msh83f8ddaec5cca20p1c8f1ajsn18e88686aab8",
        "X-RapidAPI-Host": "IBMWatsonLanguageTranslatordimasV1.p.rapidapi.com"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
    except Exception as error:
        raise KeyError(error)

    print(response.text)


if __name__ == "__main__":
    get_models()
