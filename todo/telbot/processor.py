import time


class ScheduleProcess():
    """Дополнительный процесс для обработки очереди."""

    def functions_queue():
        while True:
            cur_time = int(time.time())
            cur_time = cur_time

    def threading_process():
        from multiprocessing import Process
        p1 = Process(target=ScheduleProcess.functions_queue, args=())
        p1.start()
