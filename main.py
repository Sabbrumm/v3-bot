from threading import Thread
import time
from modules.bot_logic import infcom
from modules.bot_logic import time_checking
from modules.restarter import restarter




if __name__ == '__main__':
    th1 = Thread(target=infcom)
    th2 = Thread(target=time_checking)
    th3 = Thread(target=restarter)
    th1.start()
    time.sleep(1)
    th2.start()
    time.sleep(1)
    th3.start()
    th1.join()
    th2.join()
    th3.join()