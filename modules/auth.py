import vodka3S
import threading
from vk_api.bot_longpoll import VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from modules import bot_logic
from modules.apifuncs import send_message, longpoll, bot_session, getname
from modules.classes import User, NewUser
from modules.keyboard import fast_keyboard
import json
from vodka3S.TwoFAHelper import TwoFAHelper
from vodka3S.TokenException import TokenException
import requests
from vodka3S.TokenReceiver import TokenReceiver

def refresh_please(token):
    return TokenReceiver().get_token(token)['refreshed_token']

def captcha_getter(captcha_url, peer_id):
    session = requests.session()
    captcha_bytes = session.get(captcha_url).content
    file = open(f'captcha_messages/captcha{peer_id}.jpg', 'wb')
    file.write(captcha_bytes)
    file.close()

    server = bot_session().method('photos.getMessagesUploadServer', {'peer_id': peer_id})
    upload_url = server['upload_url']

    session = requests.session()
    resp = session.post(upload_url, files = {'photo':open(f'captcha_messages/captcha{peer_id}.jpg','rb')}).content
    photoset = json.loads(resp.decode('utf-8'))
    photo = bot_session().method('photos.saveMessagesPhoto', photoset)
    f = open(f'captcha_messages/captcha{peer_id}.jpg','w')
    f.write('0')
    f.close()
    return 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])

class DefaultUserTalk:
    def __init__(self, from_id):
        self.from_id = from_id


    ## эти потом надо засунуть во встроенки
    def get_sms_keyboard(self):
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Получить смс с кодом',
                            VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('СТОП',
                            VkKeyboardColor.NEGATIVE)

        return keyboard.get_keyboard()

    def return_result(self, result:str):
        bot_logic.registration_result[self.from_id]['answer'] = result

    def handle_captcha(self, captcha_sid, captcha_link):
        # функция обработки капчи. обязательно должна выдавать на выходе captcha_sid, captcha_key

        send_message(self.from_id, 'Введите проверочный код с картинки:', fast_keyboard(6).get_keyboard(), None,
               captcha_getter(captcha_link, self.from_id))

        captcha_key = 0

        for captcha_event in longpoll().listen():
            if captcha_event.type == VkBotEventType.MESSAGE_NEW:

                captcha_from_id = captcha_event.object.message['from_id']
                captcha_peer_id = captcha_event.object.message['peer_id']

                if self.from_id == captcha_from_id and self.from_id == captcha_peer_id:

                    captcha_key = captcha_event.object.message['text']  # присвоить пароль
                    if captcha_key == 'СТОП':
                        return 0, 0
                    break


        return captcha_sid, captcha_key

    def handle_twofa(self, validation_sid, phone_mask='defaultphonemask', previous_wrong = 0):
        # функция обработки двухфакторки. обязательно должна выдавать на выходе twofa_code
        if not previous_wrong:
            message = "Требуется двухфакторная аутентификация, введите код"
        else:
            message = "Вы ввели неверный код, попробуйте заново"
        send_message(self.from_id, message, self.get_sms_keyboard(), None, None)
        for TwoFA_event in longpoll().listen():  # слушать код двухфакторной аутентификации
            if TwoFA_event.type == VkBotEventType.MESSAGE_NEW:
                CANT_MESSAGE = 'Достигнут лимит по посланным сообщениям.\n'\
                               '\n'\
                               'Если код не пришел: \n'\
                               '-Используйте последний код, который пришел в смс\n'\
                               '-Нажмите на кнопку "СТОП", и зарегистрируйтесь заново\n'\
                               '-Дождитесь пока вам придёт код\n'\
                               '-Используйте код из приложения аутентификатора'

                TwoFA_from_id = TwoFA_event.object.message['from_id']
                TwoFA_peer_id = TwoFA_event.object.message['peer_id']
                if self.from_id == TwoFA_from_id and self.from_id == TwoFA_peer_id:
                    twofa_code = TwoFA_event.object.message['text']

                    if twofa_code == 'Получить смс с кодом':

                        try:
                            TwoFAHelper().validate_phone(validation_sid)

                            send_message(self.from_id,
                                   f"СМС выслано на номер {phone_mask}",
                                   None,
                                   None,
                                   None)

                        except TokenException as err:
                            err = err.extra
                            if 'error' in err and 'error_code' in err['error']:

                                if err['error']['error_code'] == 1112:
                                    send_message(self.from_id,
                                           "Подождите пару минут, код пока нельзя выслать",
                                           None,
                                           None,
                                           None)

                                if err['error']['error_code'] == 103:
                                    send_message(self.from_id,
                                           CANT_MESSAGE,
                                           None,
                                           None,
                                           None)
                            else:
                                send_message(self.from_id,
                                       CANT_MESSAGE,
                                       None,
                                       None,
                                       None)
                        continue
                    elif twofa_code == 'СТОП':
                        return 0
                    else:
                        return twofa_code

class autoup_register(threading.Thread):
    def __init__(self, from_id):
        super().__init__()
        self.from_id = from_id

    def return_result(self, result:str):
        bot_logic.registration_result[self.from_id]['answer'] = result

    def get_result(self):
        result = bot_logic.registration_result[self.from_id]
        del bot_logic.registration_result[self.from_id]
        return result

    def init_result(self):
        bot_logic.registration_result[self.from_id] = {}

    def null_alive(self):
        bot_logic.registration_alive[self.from_id] = []

    def greeting(self):
        send_message(self.from_id,
               'Сейчас мы попросим данные от вашего аккаунта. Это необходимо для автоматического буста.'
               'Мы не храним ваш логин и пароль. Все данные, предоставленные вами, используются только '
               'для взаимодействия с VK API.',
               None,
               None,
               None)
        self.login = None
        self.password = None

    def get_login(self):
        send_message(self.from_id, 'Введите логин:', fast_keyboard(6).get_keyboard(), None, None)
        try:
            for login_event in longpoll().listen():
                if login_event.type == VkBotEventType.MESSAGE_NEW:

                    login_from_id = login_event.object.message['from_id']
                    login_peer_id = login_event.object.message['peer_id']

                    if self.from_id == login_from_id and self.from_id == login_peer_id:

                        login = login_event.object.message['text']

                        if login == 'СТОП':
                            raise vodka3S.TokenException(vodka3S.TokenException.STOPPED, {'error': 'reg_stopped'})
                        return login
        except:
            raise vodka3S.TokenException(vodka3S.TokenException.NO_ANSWER, {'error':'reg_failed_wait'})

    def get_password(self):
        send_message(self.from_id, 'Введите пароль:', fast_keyboard(6).get_keyboard(), None, None)

        try:
            for password_event in longpoll().listen():
                if password_event.type == VkBotEventType.MESSAGE_NEW:

                    password_from_id = password_event.object.message['from_id']
                    password_peer_id = password_event.object.message['peer_id']

                    if self.from_id == password_from_id and self.from_id == password_peer_id:
                        password = password_event.object.message['text']

                        if password == 'СТОП':
                            raise vodka3S.TokenException(vodka3S.TokenException.STOPPED, {'error': 'reg_stopped'})
                        return password

        except:
            raise vodka3S.TokenException(vodka3S.TokenException.NO_ANSWER, {'error':'reg_failed_wait'})

    def auth(self):
        while True:
            #здороваемся
            self.greeting()

            try:

                #получаем логин

                self.login = self.get_login()



                # получаем пароль

                self.password = self.get_password()
                tokenres = vodka3S.get_token(self.login,
                                                   self.password,
                                                   user_talk=DefaultUserTalk(self.from_id)
                                                   )

                bot_logic.registration_result[self.from_id]['answer'] = 'success'
                bot_logic.registration_result[self.from_id]['extra'] = {'user_id': tokenres['user_id'], 'refreshed_token': tokenres['refreshed_token']}
                break

            except Exception as err:
                ext = err.extra
                if 'error' in ext:
                    if ext['error'] == 'invalid_client':
                        send_message(self.from_id,
                              'Вы ввели неверный логин или пароль. Попробуйте еще раз',
                              None, None, None)

                    if ext['error'] == 'reg_stopped':
                        send_message(self.from_id,
                               'Регистрация остановлена, напишите команду заново, когда надумаете зарегистрироваться',
                               fast_keyboard(5).get_keyboard(), None, None)
                        self.return_result('stop')
                        break

                    if ext['error'] == 'reg_failed_wait':
                        send_message(self.from_id,
                               'Закончилось время ожидания, напишите команду заново, когда надумаете зарегистрироваться',
                               fast_keyboard(5).get_keyboard(), None, None)
                        self.return_result('error')
                        break

    #TODO в аутхе норм прописать возврат

    #def is_in_db(self):
    #    return get_data("*",'users', f'user_id = {self.from_id}', None, None)!=[]

    def run(self):
        while True:
            send_message(self.from_id,
                   'Начинаю алгоритм регистрации, мы автоматически определим, от какого аккаунта вы ввели данные',
                   None, None, None)
            self.init_result()
            mainreg = threading.Thread(target= self.auth)
            mainreg.start()
            mainreg.join()

            result = self.get_result()
            print(result)

            if result['answer'] == 'error' or result['answer'] == 'stop':

                self.null_alive()
                break

            else:
                registered_user = result['extra']['user_id']
                token = result['extra']['refreshed_token']


                send_message(self.from_id, 'Входим в аккаунт...', None, None, None)
                is_fake = registered_user != self.from_id

                if not is_fake:
                    user = User(registered_user)
                    if user.token!=None:
                        send_message(self.from_id,
                                     f'Вы вошли в аккаунт {getname(registered_user)} заново. '
                                     f'Посты не будут начислены.',
                                     None,
                                     None,
                                     None)
                    else:
                        send_message(self.from_id,
                                     f'Вы вошли в аккаунт {getname(registered_user)}. '
                                     f'Мы начислили вам 1 пост.',
                                     None,
                                     None,
                                     None)
                        user.default_posts+=1

                    user.token = token
                    user.update()
                else:
                    try:
                        u = User(registered_user)
                        if u.token:
                            send_message(self.from_id,
                                         f'Вы вошли в аккаунт {getname(registered_user)} заново. '
                                         f'Он будет числиться как фейк вашего аккаунта - {getname(self.from_id)}.'
                                         f'Посты не будут начислены',
                                         None,
                                         None,
                                         None)
                    except:
                        send_message(self.from_id,
                                     f'Вы вошли в аккаунт {getname(registered_user)}. '
                                     f'Он будет числиться как фейк вашего аккаунта - {getname(self.from_id)}.'
                                     f'Мы начислим вам 1 пост.',
                                     None,
                                     None,
                                     None)

                        mainname = getname(self.from_id).split('(')[1].replace(')', '')
                        user = NewUser(registered_user, 1)
                        user.name = f'@id{registered_user}(Фейк {mainname})'
                        user.owner_id = self.from_id
                        user.token = token
                        user.insert()
                        owner = User(self.from_id)
                        owner.default_posts+=1
                        owner.update()

                send_message(self.from_id,
                       'Регистрация прошла успешно',
                       None,
                       None,
                       None)
                send_message(self.from_id,
                       'Используйте кнопки ниже для управления личным меню',
                       fast_keyboard(4).get_keyboard(),
                       None,
                       None)
            self.null_alive()
            break

