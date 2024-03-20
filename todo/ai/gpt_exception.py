import traceback


class LogTracebackExceptionError(Exception):
    """Абстракция для логирования traceback."""
    def __init__(self, message, log_traceback=True):
        super().__init__(message)
        self.log_traceback = log_traceback


class InWorkError(LogTracebackExceptionError):
    """Исключение, вызываемое, если запрос находится в работе."""
    pass


class LongQueryError(LogTracebackExceptionError):
    """Исключение для случаев, когда текст запроса слишком большой."""
    def __init__(self, message="Слишком большой текст запроса. Попробуйте сформулировать его короче."):
        self.message = message
        super().__init__(self.message)


class UnhandledError(LogTracebackExceptionError):
    """Исключение для обработки неожиданных ошибок."""
    pass


class OpenAIRequestError(LogTracebackExceptionError):
    """Ошибки, связанные с запросами к OpenAI."""
    pass


class OpenAIResponseError(OpenAIRequestError):
    """Ошибки, связанные с ответами от OpenAI."""
    pass


class OpenAIConnectionError(OpenAIRequestError):
    """Ошибки соединения при запросах к OpenAI."""
    pass


class OpenAIJSONDecodeError(OpenAIRequestError):
    """Ошибки при десериализации ответов OpenAI."""
    pass


class ValueChoicesError(OpenAIRequestError):
    """Ошибки в содержании ответа."""
    pass


async def handle_exceptions(err: Exception, need_traceback: bool = False) -> tuple[str, type, str]:
    traceback_str = ''
    traceback_err = traceback.format_exc()
    user_error_text = 'Что-то пошло не так 🤷🏼\nВозможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    error_messages = {
        InWorkError: lambda e: 'Я ещё думаю над вашим вопросом.',
        LongQueryError: lambda e: str(e),
        ValueChoicesError: lambda e: user_error_text,
        OpenAIResponseError: lambda e: 'Проблема с получением ответа от ИИ. Возможно она устала.',
        OpenAIConnectionError: lambda e: 'Проблемы соединения. Вероятно ИИ вышла ненадолго.',
        OpenAIJSONDecodeError: lambda e: user_error_text,
        UnhandledError: lambda e: user_error_text,
    }
    error_message = error_messages.get(type(err), lambda e: "Неизвестная ошибка.")(err)
    if hasattr(err, 'log_traceback') and err.log_traceback:
        err.log_traceback = need_traceback
        traceback_str = f'\n\nТрассировка:\n{traceback_err[-1024:]}'
    elif need_traceback:
        traceback_str = f'\n\nТрассировка:\n{traceback_err[-1024:]}'
    return error_message, type(err), traceback_str
