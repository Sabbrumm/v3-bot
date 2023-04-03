import datetime
import queue
import threading
import time


class SLog():
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.file = None
        self._log_queue = queue.Queue()
        self._end_logging = 0
        threading.Thread(target=self._logger).start()

    def create_log(self):
        self.file = open(f'logs/{self.filename}', 'w')
        self.file.close()
    def add_string(self, string, type='INFO'):
        q_string = f'[{datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] [{type}] {string}\n'
        self._log_queue.put(q_string)
    def _logger(self):
        time_until = 0
        while not self._end_logging:
            while not self._log_queue.empty():
                task = self._log_queue.get()
                self._add_string(task)
                self._log_queue.task_done()
            if self._log_queue.empty():
                time_until+=1
                time.sleep(1)
            if time_until>7200:
                self._end_logging=1
    def _add_string(self, string):
        self.file = open(f'logs/{self.filename}', 'r+')
        self.file.seek(0, 2)
        self.file.write(string)
        self.file.close()
    def end_logging(self):
        self._end_logging = 1
