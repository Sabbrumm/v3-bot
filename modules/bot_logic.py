import re
import time
import json
import traceback
import requests
import datetime

from vk_api.bot_longpoll import VkBotEventType
from vk_api.keyboard import VkKeyboard
from modules.classes import NewPost, User, NewUser, ArchivedUser
from modules.config import Config
from modules.keyboard import fast_keyboard
from modules.apifuncs import bot_session, longpoll, getname, send_message, delete_message, pin_message
from modules.variables import boost_enabled, get_bot_name, registered_ids, all_ids, main_peers, \
    checking_peers, subbed_users, approved_posts, staff_ids, clear_approved, wall_ids_list, \
    suggested_posts, fake_ids, admin_ids, get_user_posts, all_posts, need_to_check_posts, \
    clear_specific, bylist_users, get_user_fake_users, get_user_fake_ids, clear_fake, set_approved_boosted, \
    clear_boosted, clear_posts_from_user
from modules.databases import sql_mode
from modules.auth import autoup_register as aureg
from modules.autoup import autoup_do
from modules.variables import LISTS
from SLog import SLog
from modules.error_logging import Logger
from modules.locale import LOCALE



registration_alive = {}
registration_result = {}

now = datetime.datetime.now()
timestart = now.strftime('%y-%m-%d_%H-%M-%S')  # Запоминаем время запуска

def i_caught_error(error_desc:str):
    for peer in checking_peers():
        try:
            send_message(peer, f"Я поймал ошибку: {error_desc}.")
        except:
            pass


# Получение статуса бота
def bot_status():
    return \
        f"{get_bot_name()} by @eachbotscraft(EachBotsCraft)\n" \
        f"\n" \
        f"\n" \
        f"Бот прошел большой путь, но эксперты закрылись, и это последнее обновление в привычном понимании!\n" \
        f"В этом обновлении полностью вырезано понятие 'ап' и 'эксперты'. \n" \
        f"Вы узнаете о крупном переходе из объявлений бота\n" \
        f"'\n" \
        f"Количество пользователей на автоапе: {len(registered_ids())}/{len(all_ids())}\n" \
        f"В очереди постов: {len(all_posts())}" \
        f"\n" \
        f"Приятного использования!"


# Фунция постоянной проверки времени // ОСНОВНАЯ
def time_checking():
    alert_time_list = Config().alert_times
    drop_time_list = Config().drop_times
    ad_alert_time_list = Config().ad_alert_times
    post_reset_time_list = Config().post_reset_times
    while True:
        if datetime.datetime.now().strftime('%H:%M:%S') in alert_time_list:
            time.sleep(1)
            try:
                alert()
            except Exception as error:
                i_caught_error(str(error))
                Logger.add_string(traceback.format_exc(), 'ERROR')
                continue

        if datetime.datetime.now().strftime('%H:%M:%S') in drop_time_list:
            time.sleep(1)
            try:
                drop(0)
            except Exception as error:
                i_caught_error(str(error))
                Logger.add_string(traceback.format_exc(), 'ERROR')
                continue

        if datetime.datetime.now().strftime('%H:%M:%S') == '00:00:00':
            
            time.sleep(1)
            today_is = datetime.datetime.strptime(datetime.datetime.now().strftime('%d-%m-%Y'), '%d-%m-%Y')
            for user in subbed_users():
                sub_until = datetime.datetime.strptime(str(user.sub_until), '%d-%m-%Y')
                diff = sub_until - today_is
                if diff.days == 5:
                    try:
                        send_message(user.user_id,
                                     'Ваш срок премиум-подписки оканчивается {}\n'
                                     'Не забудьте оплатить следующий месяц!'.format(user.sub_until)
                                     )
                    except:
                        Logger.add_string(traceback.format_exc(), 'ERROR')
                if diff.days <= 0:
                    user.sub_until = None
                    user.default_posts = 1
                    user.status = "basic"
                    user.update()

                    try:
                        send_message(user.user_id,
                                     'Ваша премиум - подписка закончилась. \n'
                                     'Не забудьте оплатить следующий месяц!'.format(user.sub_until)
                                     )
                    except:
                        Logger.add_string(traceback.format_exc(), 'ERROR')

        if datetime.datetime.now().strftime('%H:%M:%S') in ad_alert_time_list:
            #time.sleep(1)
            #alert_text = get_alert_text
            #for peer in main_peers():
            #    send_message(peer, alert_text)
            pass

        if datetime.datetime.now().strftime('%H:%M:%S') in post_reset_time_list:
            time.sleep(1)
            if not Config().post_reset_after_drop:
                clear_boosted()
                for peer in main_peers():
                    try:
                        send_message(peer, 'Счётчик постов сброшен')
                    except:
                        continue


def alert():
    if approved_posts() != []:
        for peer in main_peers():
            try:
                send_message(peer, '&#10071;БУСТ БУДЕТ ЧЕРЕЗ 5 МИНУТ&#10071;')
            except:
                Logger.add_string(traceback.format_exc(), 'ERROR')

def drop(is_forsed):
    
    droplist = ['&#10071;СПИСОК ПОСТОВ В БУСТЕ&#10071;\n\n']
    droptime = datetime.datetime.now().strftime('%d.%m.%y %H:%M')

    if is_forsed:
        droplist_noindex = [f'Принудительный дроп от {droptime}\n\n']
    else:
        droplist_noindex = [f'Дроп от {droptime}\n\n']

    if approved_posts() != []:

        #генерация пост-листа
        count = 1
        for post in approved_posts():
            droplist.append(f'{count}. https://vk.com/wall{post.owner_id}_{post.post_id}')
            droplist_noindex.append(f'https://vk.com/wall{post.owner_id}_{post.post_id}')
            count += 1

        # отправка дропа в беседу
        for peer in main_peers():
            try:
                msg_id = send_message(
                    peer,
                    '\n'.join(droplist)
                )[0]['conversation_message_id']
                if Config().pin_boost_message:
                    pin_message(msg_id, peer)
            except Exception as error:
                if str(error) == '[914] Message is too long':
                    msg_id = message_separating(droplist, peer)[0]['conversation_message_id']
                    if Config().pin_boost_message and msg_id!=-1:
                        pin_message(msg_id, peer)
                else:
                    continue
        for id in staff_ids():
            try:
                send_message(
                    id,
                    '\n'.join(droplist_noindex)
                )
            except Exception as error:
                if str(error) == '[914] Message is too long':
                    message_separating(droplist_noindex, id)
                else:
                    continue

        # Часть с автоапалкой
        if boost_enabled() == True:
            for peer in checking_peers():
                send_message(peer, 'Начинаю автоап', None, None, None)
            logfile = SLog.SLog(f'boost{datetime.datetime.now().strftime("%d%m%Y-%H%M%S")}.log')
            logfile.create_log()
            autoup_do(approved_posts().copy(), logfile=logfile).start()

        # Часть с очисткой постов (зависящая от 24-часа настройки)
        if Config().post_reset_after_drop:
            clear_approved()
        else:
            set_approved_boosted()
    else:
        if not is_forsed:
            for peer in main_peers():
                send_message(peer, 'Дроп отложен')
        else:
            for peer in checking_peers():
                send_message(peer, 'Нечего дропать')


# Функция предложки // ОСНОВНАЯ ДБ
def suggesting(peer_id, from_id, attachments, cmid=None):
    
    if peer_id in main_peers():
        if len(attachments) != 0:  # если вложение есть
            if attachments[0]['type'] == 'wall':  # если вложение это пост
                attachment = attachments[0]['wall']  # вложение
                offered_post = NewPost(attachment['from_id'], attachment['id']) # подгон в формат поста
                offered_post.offered_by = from_id
                if not from_id in all_ids():  # если юзер не в списке лимитов присвоить 0 скинутых постов
                    unknown_member(from_id, peer_id)

                if offered_post.wall_id in wall_ids_list(suggested_posts()):
                    send_message(
                        peer_id,
                        'Этот пост был ранее скинут',
                    )

                else:
                    if cmid != None:
                        try:
                            if Config().delete_post_messages:
                                delete_message(cmid, peer_id)
                        except:
                            pass


                    if from_id in admin_ids():
                        offered_post.insert()
                        send_message(peer_id,
                                     str(getname(from_id) + ', твой пост успешно закинут в предложку.'),
                                     None,
                                     None,
                                     None)



                    elif from_id in fake_ids():
                        send_message(peer_id, 'Фейки не могут кидать посты')
                    else:
                        if User(from_id).summar_posts > len(get_user_posts(from_id)):
                            offered_post.insert()
                            send_message(peer_id,
                                         f'{getname(from_id)} ваш пост успешно закинут в предложку.')
                        else:
                            send_message(peer_id,
                                         f'{getname(from_id)}, ваш дневной лимит постов исчерпан!\n'
                                         '\n'
                                         'Если вы хотите заменить пост из предложки, см. команды:\n'
                                         '-Мои посты\n'
                                         '-Убрать пост\n'
                                         '\n'
                                         'Хотите увеличить лимит? Пишите администратору беседы.')


            else:
                send_message(peer_id, 'В сообщении нет поста', None, None, None)
        else:
            send_message(peer_id, 'В сообщении нет поста', None, None, None)
    else:
        send_message(peer_id, 'Это не беседа для предложки', None, None, None)

def autochecking(from_id, peer_id):
    RE_PHONE = r"/^\+?(\d{1,3})?[- .]?\(?(?:\d{2,3})\)?[- .]?\d\d\d[- .]?\d\d\d\d$/"
    RE_CARD = r"/^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$/"
    if from_id in staff_ids():  # С админкой
        if peer_id in checking_peers():  # Если беседа типа проверка
            # Счёт количества постов
            chk_posts = need_to_check_posts().copy()
            if chk_posts!=[]:
                # Рассылка о начале проверки
                keyboard = VkKeyboard(inline=False)
                send_message(peer_id,
                             'Запущен режим автопроверки постов',
                             keyboard.get_empty_keyboard()
                             )
                for peer in main_peers():
                    try:
                        send_message(peer,
                                     'АВТОПРОВЕРКА! ВСЕ ПОСТЫ НАХАЛЯВУ ПРИНЯТЫ!')
                    except:
                        continue
                for post in chk_posts:
                    post.status = 'approved'
                    post.update()

                send_message(
                    peer_id,
                    'Автопроверка окончена'
                )
            else:
                send_message(
                    peer_id,
                    f'Проверенных постов нет, либо более {Config().max_posts_per_boost}.'
                )
            #get_str = ",".join([f"{wall.owner_id}_{wall.post_id}" for wall in chk_posts])

# Функция проверки постов // ОСНОВНАЯ ДБ
def posts_checking(from_id, peer_id):
    wrong_deny = 0
    stop_checking = 0
    counter = 0
    if from_id in staff_ids():  # С админкой
        if peer_id in checking_peers():  # Если беседа типа проверка
            # Счёт количества постов
            chk_posts = need_to_check_posts().copy()
            if chk_posts!=[]:
                # Рассылка о начале проверки
                keyboard = VkKeyboard(inline=False)
                send_message(peer_id,
                             'Запущен режим проверки постов',
                             keyboard.get_empty_keyboard()
                             )
                for peer in main_peers():
                    try:
                        send_message(peer,
                                     'НАЧАЛАСЬ ПРОВЕРКА!')
                    except:
                        continue


                # Начало цикла проверки
                for post in chk_posts:
                    counter += 1
                    send_message(peer_id,
                               f'Проверено постов: {counter}/{len(chk_posts)}\n'
                               f'\n'
                               f'Пост от {User(post.offered_by).name}',
                           fast_keyboard(0).get_keyboard(),
                           None,
                           post.wall_id)  # отправка сообщения о проверке

                    while True:
                        for decision in longpoll().listen():  # слушать решение юзера по поводу поста
                            wrong_deny = 0  # ошибки в отклонении не было
                            deny = 0  # отклонения не происходило
                            stop_checking = 0  # проверка не прервана
                            if decision.type == VkBotEventType.MESSAGE_NEW and \
                                    from_id == decision.object.message['from_id'] and \
                                    peer_id == decision.object.message['peer_id']:  # 2 слушатель сообщения: прием отклон или стоп проверки
                                message = decision.object.message['text'].lower()
                                peer_id = decision.object.message['peer_id']
                                from_id = decision.object.message['from_id']

                                if 'принять' in message and \
                                        from_id in staff_ids() and \
                                        peer_id in checking_peers():
                                    post.status = 'approved'
                                    post.update()
                                    break
                                elif 'отклонить' in message and \
                                        from_id in staff_ids() and \
                                        peer_id in checking_peers():

                                    send_message(
                                        peer_id,
                                        'Назовите причину отклонения',
                                        fast_keyboard(1).get_keyboard()
                                    )

                                    for reason in longpoll().listen():  # слушать причину отклонения
                                        if reason.type == VkBotEventType.MESSAGE_NEW and \
                                                from_id == reason.object.message['from_id'] and \
                                                peer_id == reason.object.message['peer_id']:
                                            message = reason.object.message['text'].lower()
                                            peer_id = reason.object.message['peer_id']
                                            from_id = reason.object.message['from_id']
                                            if 'вернуться' in message:
                                                wrong_deny = 1
                                                # Делаем посыл поста заново
                                                send_message(peer_id,
                                                             f'Проверено постов: {counter}/{len(chk_posts)}\n'
                                                             f'\n'
                                                             f'Пост от {User(post.offered_by).name}',
                                                             fast_keyboard(0).get_keyboard(),
                                                             None,
                                                             post.wall_id)
                                                break
                                            for peer in main_peers():
                                                try:
                                                    send_message(peer,
                                                           f"{getname(post.offered_by)}, ваш пост отклонён\n"
                                                           f"Причина: {message}",
                                                           None,
                                                           None,
                                                           post.wall_id)
                                                except:
                                                    pass
                                            deny = 1  # отклонение произошло
                                            clear_specific(post.owner_id, post.post_id)
                                            break
                            if decision.type == VkBotEventType.MESSAGE_NEW and \
                                    from_id in staff_ids() and \
                                    peer_id == decision.object.message['peer_id']:
                                message = decision.object.message['text'].lower()
                                peer_id = decision.object.message['peer_id']
                                from_id = decision.object.message['from_id']
                                if 'прекратить проверку' in message and \
                                        from_id in staff_ids() and \
                                        peer_id in checking_peers():
                                    stop_checking = 1
                                    break
                            if deny == 1:
                                break
                        if wrong_deny == 0:
                            break
                    if stop_checking == 1:
                        break

                send_message(
                    peer_id,
                    'Проверка окончена'
                )
            else:
                send_message(
                    peer_id,
                    f'Проверенных постов нет, либо более {Config().max_posts_per_boost}.'
                )

        else:
            send_message(
                peer_id,
                'Это не беседа для проверки'
            )
    else:
        send_message(
            peer_id,
            LOCALE.RESPONSES.NO_RIGHTS
        )


# Функция засыла объявления // КОМАНДЫ ДБ
def announcement(peer_id, from_id):
    """Позволяет быстро дать объявление в беседы предложки"""
    keyboard = fast_keyboard(1)
    if from_id in staff_ids():
        send_message(peer_id,
               'Какое объявление вы хотите сделать?',
               keyboard.get_keyboard(),
               None,
               None)
        for announcement in longpoll().listen():
            if announcement.type == VkBotEventType.MESSAGE_NEW and from_id == \
                    announcement.object.message['from_id'] and peer_id == \
                    announcement.object.message['peer_id']:  # 2 слушатель сообщения: прием отклон или стоп проверки
                announcement_text = announcement.object.message['text']
                if 'вернуться' in announcement_text.lower():
                    break
                for peer in main_peers():
                    send_message(peer,
                           '@all ' + announcement_text)
                break
    else:
        send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)


# Функция установки диалога // КОМАНДЫ ДБ
def set_peer(from_id, peer_id, status):
    if from_id in staff_ids():
        if status == 'проверка':
            if not peer_id in checking_peers():
                send_message(peer_id, 'Теперь эта беседа - проверка')
                c = Config()
                c.checking_peers.append(peer_id)
                c.update_config()
            else:
                send_message(peer_id, 'Беседа уже является проверкой')
        if status == 'главная':
            if not peer_id in main_peers():
                send_message(peer_id, 'Теперь эта беседа - главная')
                c = Config()
                c.main_peers.append(peer_id)
                c.update_config()
                
            else:
                send_message(peer_id, 'Беседа уже является главной')
    else:
        send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)


# Функция удаления диалога // КОМАНДЫ
def del_peer(from_id, peer_id, status):
    if from_id in staff_ids():
        if status == 'проверка':
            if peer_id in checking_peers():
                send_message(peer_id, str('Эта беседа больше не проверка.'))
                c = Config()
                c.checking_peers.remove(peer_id)
                c.update_config()
            else:
                send_message(peer_id, str('Беседа ещё не является проверкой'))
        if status == 'дроп':
            if peer_id in main_peers():
                send_message(peer_id, str('Эта беседа больше не главная'))
                c = Config()
                c.main_peers.remove(peer_id)
                c.update_config()
            else:
                send_message(peer_id, str('Беседа ещё не является главной'))
    else:
        send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)


# Функция назначения участника в списке // ВАЖНО ДЛЯ ЛОГИКИ
def unknown_member(from_id, peer_id):
    try:
        user = User(from_id)
        send_message(peer_id, "Чувство дежавю! Я помню что вы выходили из беседы, но вы всё еще в моей базе!"
                              f"В любом случае, добро пожаловать снова, {user.name}!")
    except:
        try:
            user = ArchivedUser(from_id)
            user.restore_from_archive()
            send_message(peer_id, "С возвращением! Я вернул ваш аккаунт из архива, рад снова вас видеть!")
        except:
            user = NewUser(from_id, 0)
            user.insert()
            send_message(
                peer_id,
                LOCALE.RESPONSES.WELCOME_NEW(getname(from_id))
            )

def archive_on_exit(from_id, peer_id):
    try:
        user = User(from_id)
        user.move_to_archive()
        send_message(peer_id, "Кажется кто-то вышел или был исключён! Я всё видел!"
                              f"{user.name} помещён в архив!")
    except:
        send_message(peer_id, "Вы исключили очень странного человека. Либо он никогда не пользовался моими функциями,"
                              "либо уже был в архиве!\n"
                              f"Прощай, {getname(from_id)}!")

def get_user_id(string):
    if '@' in string:
        string = string.replace('@','')
    if 'vk.com/' in string:
        string = string.replace('vk.com/', '')
    if 'https://' in string:
        string = string.replace('https://', '')
    if '[' in string and '|' in string and ']' in string:
        string = string.split('|')[0].replace('[','')
    inf = bot_session().method('users.get', {'user_id':string})
    if inf == []:
        return 0
    return inf[0]['id']



def set_status(peer_id, from_id, status):
    send_message(peer_id,
                 f'Вставьте ссылку или напишите ID пользователя, которому присвоить статус {status.upper()}',
                 fast_keyboard(1).get_keyboard()
                 )
    for setst in longpoll().listen():
        if setst.type == VkBotEventType.MESSAGE_NEW:
            if setst.object.message['peer_id'] == peer_id and \
                    setst.object.message['from_id'] == from_id:
                message = setst.object.message['text'].lower()
                if 'вернуться' in message:
                    break
                else:
                    user_id = get_user_id(message)
                    if user_id == 0:
                        send_message(peer_id, 'Я не нашел такого пользователя ВКонтакте')
                        break
                    else:
                        if user_id in all_ids():
                            if not user_id in admin_ids():
                                user = User(user_id)
                                user.status = status
                                if status == 'premium':
                                    sub_until = (datetime.datetime.now()+datetime.timedelta(days=30)).strftime('%d-%m-%Y')
                                    user.sub_until = sub_until
                                user.update()

                                send_message(peer_id,
                                             'Успешно установлено')
                                send_message(peer_id, getinfo(user_id), None, None, None)
                            else:
                                send_message(peer_id,
                                             'Вы попытались совершить революцию. Вы будете наказаны! ')

                        else:
                            send_message(peer_id,
                                         'Этого пользователя нет в моей базе.',
                                         None,
                                         None,
                                         None)
                break

def set_post_count(peer_id, from_id):
    keyboard = fast_keyboard(1)
    send_message(peer_id,
           'Для кого изменить количество постов? (Вставьте ссылку или напишите ID)',
           keyboard.get_keyboard(),
           None,
           None)
    for user_postchanging in longpoll().listen():
        if user_postchanging.type == VkBotEventType.MESSAGE_NEW:
            if user_postchanging.object.message['peer_id'] == peer_id and \
                    user_postchanging.object.message['from_id'] == from_id:
                message = user_postchanging.object.message['text'].lower()
                if 'вернуться' in message:
                    break
                else:
                    user_id = get_user_id(message)
                    if user_id == 0:
                        send_message(peer_id, 'Я не нашел такого пользователя ВКонтакте', None, None, None)
                        break
                    else:
                        if user_id not in all_ids():
                            send_message(peer_id, 'Такого пользователя нет в моей базе', None, None, None)
                            break
                        else:

                            send_message(peer_id,
                                         f'Какое количество постов назначить пользователю {getname(user_id)}?',
                                         fast_keyboard(1).get_keyboard())

                            for posts_count in longpoll().listen():
                                if posts_count.type == VkBotEventType.MESSAGE_NEW:
                                    if posts_count.object.message['peer_id'] == peer_id and posts_count.object.message['from_id'] == from_id:
                                        count = posts_count.object.message['text'].lower()
                                        if 'вернуться' in count:
                                            break
                                        else:
                                            try:
                                                int(count)

                                                user = User(user_id)
                                                user.default_posts = count
                                                user.update()

                                                send_message(peer_id, f'Установил пользователю {getname(user_id)} {count} постов', None, None, None)
                                                send_message(peer_id, getinfo(user_id), None, None, None)

                                                break
                                            except:
                                                send_message(peer_id, 'Неверно указано количество постов', None, None, None)
                                                break
                            break

def show_users(peer_id, status):
    output = []
    count = 0
    if status == 'all':
        lists = LISTS.LIST_ALL
    elif status == 'basic':
        lists = LISTS.LIST_BASICS
    elif status == 'premiums':
        lists = LISTS.LIST_PREMIUMS
    elif status == 'staff':
        lists = LISTS.LIST_STAFF
    elif status == 'registered':
        lists = LISTS.LIST_REGISTERED
    elif status == 'unregistered':
        lists = LISTS.LIST_UNREGISTERED
    else:
        lists = LISTS.LIST_ALL
    for user in bylist_users(lists):
        count += 1
        output.append(f'{count}. {user.name} - {user.user_id} - {user.status} - {user.summar_posts} - Рег: {user.token==None}')
    try:
        send_message(peer_id, 'Список пользователей бота: \n' + '\n'.join(output))
    except Exception as error:
        if str(error) == '[914] Message is too long':
            message_separating(output, peer_id)


# Функция деления сообщения на несколько
def message_separating(input, peer_id):
    sep_messages = []
    each_msg = []
    cou = 0

    for string in input:
        if cou + len(string) + 6 > 4096:
            cou = 0
            sep_messages.append(each_msg)
            each_msg = []
            each_msg.append(string + '\n')
            cou += len(string) + 6
        else:
            each_msg.append(string + '\n')
            cou += len(string) + 6
    sep_messages.append(each_msg)
    msg_id = [{'conversation_message_id':-1}]
    for msg in sep_messages:
        msg_id = send_message(peer_id, ''.join(msg), None, None, None)
    return msg_id
# Отправка в беседы проверки клавиатуры
def start_attention():
    keyboard = fast_keyboard(2)
    for peer in checking_peers():
        send_message(peer, 'Я только что запустился. Все автоапы, которые были в процессе слетели.'
                           'Если актуально, перезакиньте их через личку!'
                           '\n'
                           'Любой перезапуск бота неспроста, вам очень вероятно пришел фикс!',
               keyboard.get_keyboard(), None, None)
def error_attention():
    keyboard = fast_keyboard(2)
    for peer in checking_peers():
        send_message(peer, 'Я словил ошибку. Попросите разработчика проверить логи, я должен был туда что-то записать!',
               keyboard.get_keyboard(), None, None)

def get_profiles_info(user_id):
    return_string = ''
    main_user = User(user_id)
    if main_user.token == None:
        return_string = f'Главный аккаунт:\n{getname(user_id)} - не зарегистрирован\n\n'
    else:
        return_string = f'Главный аккаунт:\n' \
                        f'{getname(user_id)} - зарегистрирован\n\n'
    fakelist = get_user_fake_users(user_id)
    if fakelist != []:
        return_string += 'Фейковые аккаунты: \n'
    for fake_user in fakelist:
        if fake_user.token == None:
            return_string += f'{getname(user_id)} - не зарегистрирован\n\n'
        else:
            return_string += f'{getname(user_id)} - зарегистрирован\n\n'
    return return_string



def getinfo(user_id):
    try:
        user = User(user_id)
    except:
        return 'Я не нашел этого пользователя в моём списке'
    status = 'Не определен'
    if user.status == 'admin':
        status = 'Главный администратор'
    if user.status == 'helper':
        status = 'Администратор'
    if user.status == 'reseller':
        status = 'Реселлер'
    if user.status == 'premium':
        status = 'Премиум'
    if user.status == 'basic':
        status = 'Базовый'
    if user.status == 'fake':
        status = 'Фейк'
    if user.token == None:
        isreg = 'Нет'
    else:
        isreg = 'Да'
    if user.sub_until == None:
        sub_until = 'Бессрочно'
    else:
        sub_until = user.sub_until
    if status != 'Фейк':
        return \
        f"Информация об участнике {getname(user_id)}:\n" \
        f"Идентификатор: {user_id}\n" \
        f"Статус: {status}\n" \
        f"Срок окончания подписки: {sub_until}\n" \
        f"Количество постов: {user.summar_posts}\n" \
        f"\n" \
        f"Зарегистрирован: {isreg}\n"
    else:
        return \
    f"Информация об участнике {getname(user_id)}\n" \
    f"Идентификатор: {user_id}\n" \
    f"Статус: {status}\n" \
    f"Владелец: {getname(user.owner_id)}\n" \

def get_token(user_id):
    try:
        token = User(user_id).token
        if token == None:
            return 'Этот пользователь не зарегистрирован в prev3'
        else:
            return token
    except:
        return 'Я не нашел этого пользователя в моёй базе'

def upload_logfile(peer, name):
    link = bot_session().method('docs.getMessagesUploadServer',{'peer_id': peer, 'type':'doc'})['upload_url']
    session = requests.Session()
    logfile = open(f'logs/{name}.log', 'rb')
    resp = session.post(link, files={'file': logfile}).content
    logfile.close()
    fileinfo = json.loads(resp.decode('utf-8'))['file']
    file = bot_session().method('docs.save', {'file': fileinfo, 'title':'logfile', 'tags':'log'})['doc']
    return f"doc{file['owner_id']}_{file['id']}"

def refresh_users():
    members = []
    members_ids = []

    new_user_names = []
    archived_user_names = []

    #просканили
    for peer in Config().main_peers:
        try:
            members += bot_session().method('messages.getConversationMembers', {'peer_id': peer})['profiles']
        except:
            continue
    for peer in Config().checking_peers:
        try:
            members += bot_session().method('messages.getConversationMembers', {'peer_id': peer})['profiles']
        except:
            continue
    #составили список айдишников
    for member in members:
        if not member['id'] in members_ids:
            members_ids.append(member['id'])

    #ишем тех кто в беседах, но не в базе:
    for member_id in members_ids:
        if not member_id in all_ids():
            try:
                us = ArchivedUser(member_id)
                us.restore_from_archive()
            except:
                us = NewUser(member_id, 0)
                us.insert()
            new_user_names.append(us.name)

    #ищем тех кто в базе, но не в беседах:
    for user_id in all_ids():
        if not user_id in members_ids:
            us = User(user_id)
            try:
                us.move_to_archive()
                archived_user_names.append(us.name)
            except:
                for chpeer in Config().checking_peers:
                    send_message(chpeer, f'Ошибка при перемещении в архив {us.name}. Позовите админа для решения вопроса')
    for peer in Config().checking_peers:
        send_message(
            peer,
            "Архивировал:\n"+
            '\n'.join(archived_user_names)+'\n'+
            'Добавил:\n'+
            '\n'.join(new_user_names)
        )
    if new_user_names:
        for peer in Config().main_peers:
            send_message(peer, 'Только что админы попросили обновить базу пользователей.\n'
                               'Теперь я знаю: '+', '.join(new_user_names)+'\n'
                               f'{LOCALE.RESPONSES.GET_RULES}')
# Логика бота

def invited_user(user_id, peer_id):
    unknown_member(user_id, peer_id)

def returned_user(user_id, peer_id):
    unknown_member(user_id, peer_id)

def link_invited_user(user_id, peer_id):
    unknown_member(user_id, peer_id)

def kicked_user(user_id, peer_id):
    clear_posts_from_user(user_id)
    archive_on_exit(user_id, peer_id)

def left_user(user_id, peer_id):
    clear_posts_from_user(user_id)
    archive_on_exit(user_id, peer_id)


def save_me(from_id):
    u = User(from_id)
    u.default_posts = Config().new_user_posts + len(get_user_fake_users(from_id)) + int((u.token is not None))
    u.referal_posts = 0
    u.update()


def commands():
    global registration_alive
    for logic in longpoll().listen():  # слушать longpoll(Сообщения)
        if logic.type == VkBotEventType.MESSAGE_NEW:

            message = logic.object.message['text'].lower()  # чтоб бот не зависел от регистра
            peer_id = logic.object.message['peer_id']  # айди диалога
            from_id = logic.object.message['from_id']
            cmid = logic.object.message['conversation_message_id']


            if 'action' in logic.object.message:
                action = logic.object.message['action']
                type_of_action = action['type']
                if peer_id in main_peers():
                    if type_of_action == 'chat_invite_user':
                        member_id = action['member_id']
                        who_added = logic.object['message']['from_id']
                        if member_id > 0:
                            if member_id != who_added:
                                invited_user(member_id, peer_id)
                            else:
                                returned_user(member_id, peer_id)
                            continue
                    if type_of_action == 'chat_invite_user_by_link':
                        member_id = logic.object['message']['from_id']
                        if member_id > 0:
                            link_invited_user(member_id, peer_id)
                            continue
                    if type_of_action == 'chat_kick_user':
                        member_id = action['member_id']
                        who_excluded = logic.object['message']['from_id']
                        if member_id > 0:
                            if member_id != who_excluded:
                                kicked_user(member_id, peer_id)
                            else:
                                left_user(member_id, peer_id)
                            continue
            if peer_id != from_id:  # если из беседы
                if from_id > 0:
                    if message == 'ping':  # пингуем бота
                        pass
                        send_message(peer_id, str(getname(from_id) + ', pong'), None, None, None)
                    if message == '/статус':
                        if Config().status_only_for_admins:
                            if from_id in staff_ids():
                                send_message(peer_id, bot_status())
                            else:
                                send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)
                        else:
                            send_message(peer_id, bot_status())
                    if "прими" in message or "#ап" in message:
                        pass
                        suggesting(peer_id, from_id, logic.object.message['attachments'], cmid)
                    if '/объявление' in message:
                        announcement(peer_id, from_id)
                        keyboard = fast_keyboard(2)
                        send_message(peer_id, 'Вы вернулись в главное меню', keyboard.get_keyboard(), None,
                               None)
                    if message == '/привет' or message == '/шалом':
                        if from_id in all_ids():
                            send_message(peer_id, 'Привет, {}!'.format(getname(from_id)), None, None, None)
                        if from_id not in all_ids() and peer_id in main_peers():
                            unknown_member(from_id, peer_id)
                    if message == '/sqlmode':
                        if from_id in admin_ids():
                            if peer_id in checking_peers():
                                send_message(peer_id, 'Вы вошли в режим SQL', fast_keyboard(1).get_keyboard(), None, None)

                                for listen_command in longpoll().listen():
                                    if listen_command.type == VkBotEventType.MESSAGE_NEW:
                                        if from_id == listen_command.object.message['from_id'] and peer_id == listen_command.object.message['peer_id']:
                                            message = listen_command.object.message['text'].lower()
                                            if 'вернуться' not in message:
                                                if 'select' in message:
                                                    send_message(peer_id, 'Я пока не поддерживаю вывод из базы данных', None, None, None)
                                                    continue
                                                else:
                                                    send_message(peer_id, str(sql_mode(message)), None, None, None)
                                            if 'вернуться' in message:

                                                send_message(peer_id, 'Вы вернулись в главное меню', fast_keyboard(2).get_keyboard(), None, None)
                                                break
                    if message == '/тип беседы':
                        if from_id in staff_ids():
                            if peer_id in checking_peers():
                                send_message(peer_id, str('Текущий тип беседы - проверка'), None, None, None)
                            elif peer_id in main_peers():
                                send_message(peer_id, str('Текущий тип беседы - главная'), None, None, None)
                            else:
                                send_message(peer_id, str('Тип беседы еще не назначен'), None, None, None)

                        else:
                            send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)
                    if '/назначить беседу' in message:
                        if len(message.split()) == 3:
                            if message.split()[2] == 'проверка' or message.split()[2] == 'главная':
                                status = message.split()[2]
                                set_peer(from_id, peer_id, status)
                            else:
                                send_message(peer_id,
                                       'Неправильный тип назначения',
                                       None,
                                       None,
                                       None)
                        else:
                            send_message(peer_id,
                                   'Неправильный тип назначения',
                                   None,
                                   None,
                                   None)
                    if '/удалить беседу' in message:
                        if len(message.split()) == 3:
                            if message.split()[2] == 'проверка' or message.split()[2] == 'главная':
                                status = message.split()[2]
                                del_peer(from_id, peer_id, status)
                            else:
                                send_message(peer_id,
                                       'Неправильный тип назначения',
                                       None,
                                       None,
                                       None)
                        else:
                            send_message(peer_id,
                                   'Неправильный тип назначения',
                                   None,
                                   None,
                                   None)
                    if '/проверка' in message:  # команда проверки
                        if from_id in staff_ids():
                            if peer_id in checking_peers():
                                send_message(peer_id, 'Выберите тип проверки', fast_keyboard(10).get_keyboard())
                                for checking_type in longpoll().listen():
                                    if checking_type.type == VkBotEventType.MESSAGE_NEW and \
                                            checking_type.object.message['peer_id'] == logic.object.message['peer_id'] and \
                                            checking_type.object.message['from_id'] == logic.object.message['from_id']:
                                        message = checking_type.object.message['text'].lower()
                                        if 'вернуться' in message:
                                            send_message(peer_id,
                                                         'Вы вернулись в главное меню',
                                                         fast_keyboard(2).get_keyboard())
                                            break
                                        if 'проверка постов' in message:
                                            posts_checking(from_id, peer_id)
                                            send_message(peer_id,
                                                         'Вы вернулись в главное меню',
                                                         fast_keyboard(2).get_keyboard())
                                            break
                                        if 'автопроверка' in message:
                                            autochecking(from_id, peer_id)
                                            send_message(peer_id,
                                                         'Вы вернулись в главное меню',
                                                         fast_keyboard(2).get_keyboard())
                    if '/дроп' in message:  # скидывает посты по беседам дроп
                        if from_id in staff_ids():
                            drop(1)
                        else:
                            send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)
                    if '/мои посты' in message:
                        if from_id in all_ids():
                            user_posts = get_user_posts(from_id)
                            output = []
                            if len(user_posts) > 0:
                                for i in range(len(user_posts)):
                                    output.append(f'{i+1}. https://vk.com/{user_posts[i].wall_id} - {user_posts[i].status_ru}')
                                send_message(peer_id, 'Ваш список постов за сегодня:\n' + '\n'.join(
                                    output) + '\n\nЕсли вы хотите удалить какой-либо пост из списка, используйте команду "/убрать пост [номер поста]"',
                                       None, None, None)
                            else:
                                send_message(peer_id,
                                       'Вы сегодня не кидали посты\n\nЕсли вы хотите добавить пост в предложку, используйте команду "/прими"',
                                       None, None, None)
                        else:
                            unknown_member(from_id, peer_id)
                    if '/убрать пост' in message:

                        if len(message.split(' ')) == 3:
                            try:
                                post_number = int(message.split(' ')[2])
                                user_post_list = get_user_posts(from_id)
                                if post_number <= len(user_post_list):
                                    deletedpost = user_post_list[post_number - 1]
                                    if deletedpost.status == 'suggested':
                                        send_message(peer_id,
                                                     'Из вашей предложки был исключен пост: https://vk.com/' +
                                                     user_post_list[post_number - 1].wall_id, None, None, None)

                                        clear_specific(deletedpost.owner_id, deletedpost.post_id)
                                    else:
                                        send_message(peer_id, 'Этот пост уже ушел в буст! Его нельзя удалить!')

                                else:
                                    send_message(peer_id, 'Такого поста нет в списке. Используйте номер из личного списка постов\n\nПосмотреть: /мои посты', None, None, None)
                            except Exception as error:
                                if 'invalid literal for int()' in str(error):
                                    send_message(peer_id,
                                           'Неправильный формат удаления поста! \n\nНапример: /убрать пост 1',
                                           None, None, None)
                        else:
                            send_message(peer_id,
                                   'Неправильный формат удаления поста! \n\nНапример: /убрать пост 1',
                                   None, None, None)
                    if '/параметры' in message:
                        if from_id in staff_ids():
                            if peer_id in checking_peers():
                                keyboard = fast_keyboard(3)
                                send_message(peer_id, 'Выберите команду на клавиатуре', keyboard.get_keyboard(), None, None)
                                for parameters in longpoll().listen():
                                    if parameters.type == VkBotEventType.MESSAGE_NEW:
                                        if parameters.object.message['from_id'] == from_id and parameters.object.message[
                                            'peer_id'] == peer_id:
                                            message = parameters.object.message['text'].lower()


                                            if 'список админов' in message:
                                                keyboard = VkKeyboard(inline=False)
                                                send_message(peer_id, 'Ищу админов в базе...', keyboard.get_empty_keyboard(), None, None)

                                                show_users(peer_id, 'staff')
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)
                                            if 'список всех' in message:
                                                send_message(peer_id,
                                                       'Ищу пользователей в базе...',
                                                       keyboard.get_empty_keyboard(), None, None)

                                                show_users(peer_id, 'all')
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id, 'Выберите команду на клавиатуре', keyboard.get_keyboard(),
                                                       None, None)

                                            if 'список премиумов' in message:
                                                keyboard = VkKeyboard(inline=False)
                                                send_message(peer_id, 'Ищу премиумов в базе...', keyboard.get_empty_keyboard(),
                                                       None, None)

                                                show_users(peer_id, 'premiums')
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)
                                            if 'список зарегистрированных' in message:
                                                keyboard = VkKeyboard(inline=False)
                                                send_message(peer_id, 'Ищу зарегистрированных в базе...', keyboard.get_empty_keyboard(),
                                                       None, None)

                                                show_users(peer_id, 'registered')
                                                show_users(peer_id, 'unregistered')
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)

                                            if 'назначить статус basic' in message:

                                                set_status(peer_id, from_id, 'basic')

                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)

                                            if 'назначить статус premium' in message:

                                                set_status(peer_id, from_id, 'premium')

                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)

                                            if 'назначить статус helper' in message:

                                                set_status(peer_id, from_id, 'helper')

                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)

                                            if 'назначить посты' in message:

                                                set_post_count(peer_id, from_id)
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                       'Выберите команду на клавиатуре',
                                                       keyboard.get_keyboard(),
                                                       None,
                                                       None)

                                            if 'обновить базу юзеров' in message:
                                                refresh_users()
                                                keyboard = fast_keyboard(3)
                                                send_message(peer_id,
                                                             'Выберите команду на клавиатуре',
                                                             keyboard.get_keyboard(),
                                                             None,
                                                             None)

                                            if 'включить автоап' in message:

                                                if boost_enabled() == False:
                                                    c = Config()
                                                    c.global_boost = 1
                                                    c.update_config()
                                                    send_message(peer_id, 'Теперь АвтоАп включен', fast_keyboard(3).get_keyboard(), None, None)

                                            if 'выключить автоап' in message:

                                                if boost_enabled() == True:
                                                    c = Config()
                                                    c.global_boost = 0
                                                    c.update_config()
                                                    send_message(peer_id, 'Теперь АвтоАп выключен', fast_keyboard(3).get_keyboard(), None, None)

                                            if 'закрыть параметры' in message:
                                                keyboard = fast_keyboard(2)
                                                send_message(peer_id, 'Параметры закрыты', keyboard.get_keyboard(), None, None)
                                                break
                            else:
                                send_message(peer_id, 'Неверный тип беседы для команды', None, None, None)
                        else:
                            send_message(peer_id, LOCALE.RESPONSES.NO_RIGHTS)
                    if message == '/помощь' or message == '/команды':
                        send_message(peer_id,
                                     """Список команд:
                     
                                     "ping" - Если бот отвечает "pong" значит он исправно работает
                     
                                     "/правила" - выводит ссылку на правила бота
                     
                                     "/прими" (допустим вариант "Прими") - принимает ваш пост в предложенные посты
                     
                                     "/мои посты" - выводит список ваших постов за сегодня
                     
                                     "/убрать пост [номер]" - убирает пост из списка ваших постов по номеру
                     
                                     "регистрация" - РАБОТАЕТ ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ
                                     Запускает алгоритм регистрации для автоапа
                     
                                     "/привет" - знакомится с новыми пользователями, здоровается со старыми
                     
                                     "/статус" - выводит версию бота, количество автоаперов и очередь постов""",
                                     None,
                                     None,
                                     None)
                    if message == '/правила':
                        pass
                        send_message(peer_id, LOCALE.RESPONSES.GET_RULES, None, None,
                                     None)

            if peer_id == from_id:  # если из лс
                if from_id in all_ids():
                    if 'регистрация' in message and message!='регистрация':
                        send_message(from_id, 'Вы написали неверную команду! Напишите Регистрация')

                    if message == 'регистрация':
                        try:
                            if not from_id in registration_alive:
                                registration_alive[from_id] = []
                            thread = aureg(from_id)
                            registration_alive[from_id].append(thread)
                            if registration_alive[from_id][0].is_alive() == False:
                                registration_alive[from_id][0].start()
                            else:
                                if len(registration_alive[from_id]) > 1:
                                    registration_alive[from_id]=registration_alive[from_id][:1]
                                    send_message(from_id, 'Вы уже регистрируетесь! Нажмите на кнопку СТОП для отмены регистрации', None, None, None)
                        except Exception as error:
                            print(error)
                            Logger.add_string(traceback.format_exc(), 'ERROR')
                            send_message(213442796, 'ОШИБКА В МОДУЛЕ РЕГИСТРАЦИИ!\n' + str(error), None, None, None)
                            continue


                    if message == 'выйти из аккаунта':
                        if from_id in registered_ids():
                            u = User(from_id)
                            u.token = None
                            u.default_posts-=1
                            u.update()
                            if get_user_fake_ids(from_id) == []:
                                send_message(
                                    from_id,
                                    'Вы успешно вышли из аккаунта. '
                                    'Для повторного входа напишите "Регистрация"',
                                    fast_keyboard(5).get_keyboard()
                                )
                            else:
                                send_message(
                                    from_id,
                                    f'Вы успешно вышли с вашего основного аккаунта {getname(from_id)}'
                                    f'Учтите, что Ваши фейки до сих пор в базе v3',
                                    fast_keyboard(7).get_keyboard()
                                )
                                

                        else:
                            send_message(from_id, 'Вы еще не зарегистрированы.', None, None, None)

                    if message == 'мой профиль':
                        if from_id in registered_ids():
                            try:
                                
                                send_message(from_id, getinfo(from_id))
                                send_message(from_id, 'Ваш токен:')
                                send_message(from_id, get_token(from_id), fast_keyboard(4).get_keyboard(), None, None)
                            except Exception as error:
                                Logger.add_string(traceback.format_exc(), 'ERROR')
                        else:
                            try:
                                send_message(from_id, 'Вы не зарегистрированы', None, None, None)
                            except:
                                pass

                    if message == 'список аккаунтов':
                        send_message(from_id, get_profiles_info(from_id), None, None, None)
                    if message == 'дополнительные команды':
                        send_message(from_id, '''Дополнительные команды, которые не включены в личное меню:

-Удалить аккаунт {ссылка на аккаунт}: удалит ваш фейк из базы, если он до этого был зарегистрирован

-Информация о {ссылка на аккаунт}: выведет информацию об одном из ваших аккаунтов.''', None, None, None)
                    if message == 'спасительная кнопка':
                        send_message(from_id, 'Заново обрабатываю ваш аккаунт...', VkKeyboard.get_empty_keyboard(), None, None)
                        
                        save_me(from_id)
                        
                        send_message(from_id, 'Ваши аккаунты обработаны заново. ', None, None, None)
                        send_message(from_id, get_profiles_info(from_id), fast_keyboard(4).get_keyboard(), None, None)
                    if 'информация о' in message:
                        if len(message.split()) == 3 and message.split()[0] == 'информация' and message.split()[1] == 'о':
                            account_id = get_user_id(message.split()[2])
                            if account_id == 0:
                                send_message(from_id, 'Я не смог найти такой аккаунт ВКонтакте', None, None, None)
                            else:
                                if account_id in get_user_fake_ids(from_id) or account_id == from_id:
                                    send_message(from_id, getinfo(account_id), None, None, None)
                                    send_message(from_id, 'Токен аккаунта:', None, None, None)
                                    send_message(from_id,
                                                 get_token(account_id),
                                                 fast_keyboard(4).get_keyboard()
                                                 )
                                else:
                                    send_message(from_id,
                                                 'Это не ваш аккаунт, либо он ещё не зарегистрирован. '
                                                 'Я не могу предоставить вам данные о нём')

                    if 'удалить аккаунт' in message:
                        if len(message.split()) == 3 and message.split()[0] == 'удалить' and message.split()[
                            1] == 'аккаунт':
                            account_id = get_user_id(message.split()[2])
                            if account_id == 0:
                                send_message(from_id, 'Я не смог найти такой аккаунт ВКонтакте', None, None, None)
                            else:
                                if account_id in get_user_fake_ids(from_id):
                                    
                                    clear_fake(account_id)
                                    u = User(from_id)
                                    u.default_posts-=1
                                    u.update()

                                    if get_user_fake_ids(from_id) == [] and User(from_id).token == None:
                                        send_message(from_id,
                                                     'Я удалил из своей базы этот аккаунт. '
                                                     'Теперь ни один ваш аккаунт не зарегистрирован',
                                                     fast_keyboard(5).get_keyboard(), None, None)

                                    elif get_user_fake_ids(from_id)!=[] and User(from_id).token == None:
                                        send_message(from_id,
                                                     'Я удалил из своей базы этот аккаунт. '
                                                     'Ваш основной аккаунт не зарегистрирован.',
                                                     fast_keyboard(4).get_keyboard(), None, None)

                                    elif get_user_fake_ids(from_id) == [] and User(from_id).token != None:
                                        send_message(from_id,
                                                     'Я удалил из своей базы этот аккаунт.'
                                                     'У вас остался зарегистрированным только основной аккаунт.',
                                                     fast_keyboard(4).get_keyboard(), None, None)

                                    elif get_user_fake_ids(from_id) != [] and User(from_id).token != None:
                                        send_message(from_id,
                                               'Я удалил из своей базы этот аккаунт.',
                                               fast_keyboard(4).get_keyboard())
                                else:
                                    send_message(from_id, 'Это не ваш аккаунт, или вы ввели главный аккаунт. '
                                                          'Я не могу его удалить.')
                    #Админские команды
                    if '/автолайкнуть:' in message:
                        if from_id in staff_ids():
                            postlist = message.replace('/автолайкнуть:', '').split('\n')[1:]
                            filtered = []
                            if postlist == []:
                                send_message(from_id, 'Неправильный формат сообщения', None, None, None)
                            else:
                                for post in postlist:
                                    if 'https://vk.com/wall' in post and '_' in post:
                                        owner_id = post.replace('https://vk.com/wall', '').split('_')[0]
                                        post_id = post.replace('https://vk.com/wall', '').split('_')[1]
                                        try:
                                            int(owner_id)
                                            int(post_id)
                                            filtered.append(post.replace('\n', '').replace('https://vk.com/', ''))
                                        except:
                                            send_message(from_id, 'Неправильный формат поста, исключаю: {}'.format(post),
                                                   None, None, None)
                                    else:
                                        send_message(from_id, 'Неправильный формат поста, исключаю: {}'.format(post),
                                               None,
                                               None, None)
                                print(filtered)
                                if filtered:
                                    send_message(from_id, 'Автоап с лайками запущен', None, None, None)
                                    logfile = SLog.SLog(f'boost{datetime.datetime.now().strftime("%d%m%Y-%H%M%S")}.log')
                                    logfile.create_log()
                                    posts = [NewPost(
                                        i.replace("wall", "").split('_')[0],
                                        i.replace("wall", "").split('_')[1]
                                        ) for i in filtered]
                                    autoup_do(posts, logfile=logfile).start()
                                else:
                                    send_message(from_id, 'Неправильный формат сообщения', None, None, None)
                    if 'абобус инфо' in message:
                        if from_id in staff_ids():
                            if len(message.split()) == 3:
                                if message.split()[0] == 'абобус' and message.split()[1] == 'инфо':
                                    user = get_user_id(message.split()[2])
                                    if user == 0:
                                        send_message(from_id, 'Я не нашел такого пользователя ВКонтакте', None, None, None)
                                    else:
                                        send_message(from_id, getinfo(user), None, None, None)
                    if 'абобус токен' in message:
                        if from_id in admin_ids():
                            if len(message.split()) == 3:
                                if message.split()[0] == 'абобус' and message.split()[1] == 'токен':
                                    user = get_user_id(message.split()[2])
                                    if user == 0:
                                        send_message(from_id, 'Я не нашел такого пользователя ВКонтакте', None, None, None)
                                    else:
                                        send_message(from_id, get_token(user), None, None, None)

                else:
                    send_message(from_id, 'Я вас не знаю... Попробуйте обратиться к администрации проекта', None, None, None)

# ФУНКЦИЯ БЕСКОНЕЧНОГО ПОВТОРЕНИЯ ПРИ ВЫЛЕТЕ // ВАЖНАЯ ДЛЯ ЛОГИКИ
def infcom():
    start_attention()
    while True:
        try:
            commands()
        except Exception as err:
            Logger.add_string(traceback.format_exc(), 'ERROR')
            if not 'Read timed out' in str(err):
                error_attention()
            continue