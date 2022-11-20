import threading
import time

from .qu_events import main_process_distributor, send_forismatic_quotes


class ScheduleProcess:
    """Дополнительный процесс и очередь обработки."""

    def functions_queue():
        while True:
            cur_time = time.localtime()
            cur_time = cur_time

            if cur_time.tm_sec == 0:
                main_process_distributor(cur_time)

            if cur_time.tm_hour == 0 and cur_time.tm_min == 0:
                send_forismatic_quotes()

    def threading_process():

        main_thread = threading.Thread(
            target=ScheduleProcess.functions_queue, args=()
        )
        main_thread.start()
