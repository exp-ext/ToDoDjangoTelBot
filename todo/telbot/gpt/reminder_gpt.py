import traceback

from ai.gpt_exception import handle_exceptions
from ai.gpt_query import GetAnswerGPT
from channels.db import database_sync_to_async
from django.db.models import Model
from telbot.models import GptModels, ReminderAI


class ReminderGPT(GetAnswerGPT):

    def __init__(self, text: str, user: 'Model', chat_id: int) -> None:
        query_text = text
        assist_prompt = self.init_model_prompt
        history_model = ReminderAI
        self.chat_id = chat_id
        super().__init__(query_text, assist_prompt, user, history_model, self.chat_id, 0.1)

    async def transform(self) -> None:
        try:
            await self.get_answer_chat_gpt()
        except Exception as err:
            _, type_err = await handle_exceptions(err)
            if hasattr(err, 'log_traceback') and err.log_traceback:
                err.log_traceback = False
            else:
                traceback_str = traceback.format_exc()
                add_err_trace = f'\n\nТрассировка:\n{traceback_str[-1024:]}'
            raise type_err(f'Ошибка в процессе `ReminderGPT`: {err}{add_err_trace}') from err
        return self.return_text

    async def get_prompt(self) -> None:
        self.all_prompt = [
            {'role': 'system', 'content': self.init_model_prompt},
            {'role': 'user', 'content': self.query_text}
        ]

    @database_sync_to_async
    def init_user_model(self) -> None:
        self.model = GptModels.objects.filter(default=True).first()

    @property
    def init_model_prompt(self) -> str:
        return """
            ЧатGPT, я прошу Вас преобразовать следующий текст в формат:
            «дата {числовой формат} время {числовой формат}
            | количество минут за сколько оповестить до наступления дата+время {по умолчанию: 120}
            | повтор напоминания {по умолчанию: N, каждый день: D, каждую неделю: W, каждый месяц: M, каждый год: Y}
            | тело напоминания {исправить ошибки}».
            Ответ для примера: «20.11.2025 17:35|30|N|Запись к врачу»
            """
