from modules.config import Config
import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll

def bot_token():
    return Config().bot_token
def bot_session():
    bot_session = vk_api.VkApi(token=bot_token())
    bot_session._auth_token()
    return bot_session

def longpoll():
    longpoll = VkBotLongPoll(bot_session(), int(group_id()))
    return longpoll
def group_id():
    return Config().group_id
def vk():
    vk = bot_session().get_api()
    return vk

# Функция получения имени пользователя // ВАЖНАЯ ДЛЯ ЛОГИКИ
def getname(id):
    if id>=0:
        try:
            user_get = vk().users.get(user_ids=(id))
            name = user_get[0]['first_name']
            surname = user_get[0]['last_name']
            return f'@id{id}({name} {surname})'
        except:
            return f'@id{id}(Unknown Name)'
    else:
        try:
            user_get = vk().groups.getById(group_ids=(-1*id))
            scrname = user_get[0]['screen_name']
            name = user_get[0]['name']
            return f'@{scrname}({name})'
        except:
            return f'Unknown Public'

def send_message(id, text, keyboard=None, template=None, attachment=None):
    return bot_session().method('messages.send',
                       {'peer_ids': id, 'message': text, 'random_id': get_random_id(), 'keyboard': keyboard,
                        'template': template, 'attachment': attachment, 'v':'5.131'})

def delete_message(message_id, chat_id):
    bot_session().method('messages.delete',
                     {'cmids': message_id, 'group_id': int(group_id()), 'delete_for_all': 1, 'peer_id': chat_id})

def pin_message(cmid, peer_id):
    bot_session().method('messages.pin',
                     {'conversation_message_id': cmid, 'peer_id': peer_id})