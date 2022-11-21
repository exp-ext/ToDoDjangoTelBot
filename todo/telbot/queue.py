import time
from threading import Thread

from .qu_events import main_process_distributor, send_forismatic_quotes


class ScheduleProcess:
    """Дополнительный процесс и очередь обработки."""

    def functions_queue():
        while True:
            time.sleep(1)
            cur_time = int(time.time())
            localtime = time.localtime()

            if cur_time % 60 == 0:
                t1 = Thread(
                    group=None,
                    target=main_process_distributor,
                    args=(cur_time,)
                )
                t1.start()

            if (localtime.tm_hour == 10 and localtime.tm_min == 0
                    and localtime.tm_sec == 0):
                t2 = Thread(
                    group=None,
                    target=send_forismatic_quotes,
                    args=()
                )
                t2.start()

    def threading_process():

        main_thread = Thread(
            target=ScheduleProcess.functions_queue, args=()
        )
        main_thread.start()
