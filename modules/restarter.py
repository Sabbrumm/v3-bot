import os
import time
import traceback

from vk_api.bot_longpoll import VkBotEventType

from modules.apifuncs import longpoll, send_message
from modules.config import Config
from modules.error_logging import Logger
from modules.variables import staff_ids


def restarter():
    while True:
        try:
            for restart in longpoll().listen():  # слушать longpoll(Сообщения)
                if restart.type == VkBotEventType.MESSAGE_NEW:
                    message = restart.object.message['text'].lower()  # чтоб бот не зависел от регистра
                    peer_id = restart.object.message['peer_id']  # айди диалога
                    from_id = restart.object.message['from_id']
                    if not 'action' in restart.object.message:
                        if from_id in staff_ids():
                            if message == '/рестарт':
                                send_message(peer_id, 'Перезапускаюсь...', None, None, None)
                                os.system(f'systemctl restart {Config().bot_dev_name}')
                                time.sleep(3)
                                print('После этого сообщения бот должен релоаднуться.')
                                exit(1)
        except:
            Logger.add_string(traceback.format_exc(), 'ERROR')
            continue