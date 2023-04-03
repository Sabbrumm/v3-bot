from SLog.SLog import SLog
import datetime

Logger = SLog(f'logging{datetime.datetime.now().strftime("%d%m%Y-%H%M%S")}.log')
Logger.create_log()