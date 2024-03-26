from ai.gpt_exception import handle_exceptions
from ai.gpt_query import GetAnswerGPT
from channels.db import database_sync_to_async
from django.db.models import Model
from telbot.models import GptModels, ReminderAI


class ReminderGPT(GetAnswerGPT):

    def __init__(self, text: str, user: 'Model', chat_id: int) -> None:
        query_text = text
        history_model = ReminderAI
        self.chat_id = chat_id
        creativity_controls = {
            'temperature': 0.1,
            'top_p': 0.5,
        }
        super().__init__(query_text, user, history_model, self.chat_id, creativity_controls)

    async def transform(self) -> None:
        try:
            await self.get_answer_chat_gpt()
        except Exception as err:
            _, type_err, traceback_str = await handle_exceptions(err, True)
            raise type_err(f'Ошибка в процессе `ReminderGPT`: {err}{traceback_str}') from err
        return self.return_text

    async def get_prompt(self) -> None:
        self.all_prompt = [
            {'role': 'system', 'content': self.assist_prompt},
            {'role': 'user', 'content': self.query_text}
        ]

    @database_sync_to_async
    def init_user_model(self) -> None:
        self.model = GptModels.objects.filter(default=True).first()

    @property
    def assist_prompt(self) -> str:
        return """
            ЧатGPT, я прошу Вас преобразовать следующий текст в формат:
            «дата {числовой формат} время {числовой формат}
            | количество минут за сколько оповестить до наступления дата+время {по умолчанию: 120}
            | повтор напоминания {по умолчанию: N, каждый день: D, каждую неделю: W, каждый месяц: M, каждый год: Y}
            | тело напоминания {исправить ошибки}».
            Ответ для примера: «20.11.2025 17:35|30|N|Запись к врачу»
            """
