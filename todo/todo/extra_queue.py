import time
from datetime import datetime
from threading import Thread

from telbot.tasks import main_process_distributor, send_forismatic_quotes


class ScheduleProcess:
    """Дополнительный процесс и очередь обработки."""

    def functions_queue():
        while True:
            time.sleep(60)
            this_datetime = datetime.utcnow().replace(second=0, microsecond=0)

            t1 = Thread(
                group=None,
                target=main_process_distributor,
                args=()
            )
            t1.start()

            if this_datetime.hour == 10 and this_datetime.minute == 30:
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
