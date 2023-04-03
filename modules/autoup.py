import threading

from SLog import SLog
import time
import random

from modules.apifuncs import send_message, getname
from modules.variables import registered_users, checking_peers, clear_fake
from modules.classes import User, Post
from modules.auth import refresh_please

class Settings(object):
    def __init__(self):
        self.autolikes = 1
        self.autoups = 1
        self.max_capthcas = 4
        self.search_delay_min = 30
        self.search_delay_max = 50

        self.uplike_delay_min = 3
        self.uplike_delay_max = 9

        self.watch_delay_min = 14
        self.watch_delay_max = 30

        self.good_post_likes = 80
        self.good_post_views = 3000
        self.good_post_count = 1
        self.posts_per_load = 14




class autoup_user(threading.Thread):
    def __init__(self, user:User, postlist: list, is_im=0, logfile:SLog.SLog = None):
        super().__init__()
        self.user = user
        self.postlist = postlist
        random.shuffle(self.postlist)
        self.is_im = is_im
        self.logfile = logfile
        self.captchas = 0
        self.startfrom = None
        self.online_counter = 0

    def run(self):
        self.log(f'Начал буст с аккаунта {self.user.user_id}')
        try:
            self.online()
        except Exception as error:
            self.handle_errors(error)
        postlist = self.postlist.copy()[:Settings().posts_per_load]
        while self.postlist!=[]:
            random.shuffle(postlist)
            for post in postlist:
                self.like_this_post = 0
                try:
                    time.sleep(self.get_search_delay())

                    self.watch(post)
                except Exception as error:
                    self.handle_errors(error)
                    continue


                try:
                    time.sleep(self.get_watch_delay())
                    if self.like_this_post:
                        self.like(post)
                    else:
                        self.log(f'{self.user.user_id}: Лайк не нужно ставить'
                                 f'https://vk.com/wall{post.owner_id}_{post.post_id}')
                except Exception as error:
                    self.handle_errors(error)
                    continue
                try:
                    self.remove_post_from_postlist(post)
                    self.online_counter+=1
                    if self.online_counter>=5:
                        if not self.online():
                            self.critical_stop()
                except Exception as error:
                    self.handle_errors(error)
                    continue
            postlist = self.postlist.copy()[:Settings().posts_per_load]
    def like(self, post:Post):
        try:

            if Settings().autolikes:

                self.user.vk_session.method('likes.add',
                                       {'type': 'post', 'owner_id': int(post.owner_id), 'item_id': int(post.post_id)})

                self.log(f'{self.user.user_id}: Поставлен лайк '
                                        f'https://vk.com/wall{post.owner_id}_{post.post_id}')
        except Exception as error:

            self.log(f'{self.user.user_id}: Не получилось лайкнуть пост '
                                    f'https://vk.com/wall{post.owner_id}_{post.post_id}, '
                                    f'err={str(error)}',
                                    'ERROR')
            raise Exception(f"Like Exception: {str(error)}")
    def online(self):
        try:

            self.user.vk_session.method('account.setOnline', {'voip': 1})

            self.log(f'{self.user.user_id}: Совершён вход в онлайн')

            self.online_counter = 0

            return 1
        except Exception as error:

            self.log(f'{self.user.user_id}: Не получилось войти в онлайн, err={str(error)}',
                                    'ERROR')

            raise Exception(f"Online Exception: {str(error)}")
    def watch(self, post):
        try:

            wall = self.user.vk_session.method('wall.getById', {'posts': f'{post.owner_id}_{post.post_id}', 'extended': 1})['items']

            if len(wall) == 1 and 'is_deleted' in wall[0] and wall[0]['is_deleted'] == True:

                self.log(f'{self.user.user_id}: Пост удалён, пропускаю '
                         f'https://vk.com/wall{post.owner_id}_{post.post_id}')
                return 0

            if len(wall) == 1 and \
                'likes' in wall[0] and \
                'can_like' in wall[0]['likes'] and \
                wall[0]['likes']['can_like'] == 1:
                self.like_this_post = 1
            self.log(f'{self.user.user_id}: Просмотрен пост'
                                    f'https://vk.com/wall{post.owner_id}_{post.post_id}')

            return 1
        except Exception as error:

            self.logfile.add_string(f'{self.user.user_id}: Не получилось просмотреть пост '
                                    f'https://vk.com/wall{post.owner_id}_{post.post_id}, '
                                    f'err={str(error)}',
                                    'ERROR')
            raise Exception(f"Watch Exception: {str(error)}")
    def remove_post_from_postlist(self, post:Post):
        for post2 in self.postlist.copy():
            if post2.owner_id == post.owner_id and post2.post_id == post.post_id:
                self.postlist.remove(post2)
                break
    def critical_stop(self, reason='Just Stop'):
        raise Exception(f'Critical stop: {reason}')
    def handle_errors(self, error):
        if 'User authorization' in str(error):
            if self.user.status != 'fake':
                try:
                    send_message(self.user.user_id, 'Ваш токен больше недействителен, просьба авторизоваться заново.',
                           None,
                           None, None)
                except:

                    self.log(f'{self.user.user_id}: Токен недействителен, '
                             f'нет связи с владельцем аккаунта'
                             f'(https://vk.com/id{self.user.user_id})', 'ERROR')

                finally:
                    self.user.token = None
                    self.user.default_posts -= 1
                    self.user.update()
                    self.critical_stop()

            else:
                owner = self.user.owner_id
                if owner != None:
                    try:
                        send_message(owner,
                               f'Токен вашего фейка {getname(self.user.user_id)} больше недействителен. Авторизуйте его заново.',
                               None, None, None)
                    except:

                        self.log(f'{self.user.user_id}: Токен недействителен, '
                                 f'нет связи с владельцем фейка '
                                 f'(https://vk.com/id{owner})', 'ERROR')

                    finally:
                        clear_fake(self.user.user_id)
                        self.critical_stop()
                else:
                    self.log(f'{self.user.user_id}: Токен недействителен, '
                             f'владельца нет '
                             f'(https://vk.com/id{owner})', 'ERROR')
                    clear_fake(self.user.user_id)
                    self.critical_stop()
        if 'User is deactivated' in str(error) or 'user is blocked' in str(error):
            self.log(f'Пользователя заблокировало. {self.user.name}', 'ERROR')
            self.user.token = None
            self.user.default_posts-=1
            self.user.update()
            self.critical_stop('Deactivated user')
        elif 'Too late for vote' in str(error):
            pass
        elif 'Rate limit reached' in str(error):
            self.critical_stop()
        elif '[9] Flood control' in str(error) or 'Captcha needed' in str(error) or 'Validation required' in str(error):
            if self.captchas < Settings().max_capthcas:
                self.captchas += 1
                time.sleep(random.randint(40, 60))
            else:
                self.log(f'{self.user.user_id}: Автоап окончен, слишком много ошибок!', 'ERROR')
                self.critical_stop('Break Priority reached')

        elif 'Token confirmation required' in str(error) or 'Client version deprecated' in str(error):
            if self.captchas < Settings().max_capthcas:
                self.log(f'{self.user.user_id}: Пытаюсь рефрешнуть токен')

                try:
                    self.token = refresh_please(self.user.token)
                    self.captchas += 1
                    self.user.token = self.token
                    self.user.update()
                    self.user = User(self.user.user_id)
                    self.log(f'{self.user.user_id}: Успешный рефреш')

                except Exception as err:
                    self.log(f'{self.user.user_id}: Ошибка при рефреше: {err}')
                    raise Exception(f'Refresh error: {err}')
            else:
                self.log(f'{self.user.user_id}: Автоап окончен, слишком много ошибок!', 'SUPERROR')
                raise Exception('Break Priority reached')
        else:
            self.log(f'{self.user.user_id} - неизвестная ошибка '
                     f'{str(error)}', 'ERROR_UNKNOWN')
            self.captchas += 1
    def get_search_delay(self):
        return round(
            random.uniform(
                Settings().search_delay_min,
                Settings().search_delay_max
            ),
            2
        )
    def get_uplike_delay(self):
        return round(
            random.uniform(
                Settings().uplike_delay_min,
                Settings().uplike_delay_max
            ),
            2
        )
    def get_watch_delay(self):
        return round(
            random.uniform(
                Settings().watch_delay_min,
                Settings().watch_delay_max
            ),
            2
        )
    def log(self, string, type='INFO'):
        if self.logfile!=None:
            self.logfile.add_string(string, type)
            print(f"{type}:::: {string}")
        else:
            print(f"{type}:::: {string}")

class autoup_do:
    def __init__(self, postlist, logfile:SLog.SLog=None, report_message_id:int=None):
        self.postlist = postlist
        self.logfile = logfile
        self.report_message_id = report_message_id
    def start(self):
        n = threading.Thread(target=self.autoup_thread, args=(self.postlist, self.logfile, self.report_message_id,))
        n.start()
    def autoup_thread(self, postlist, logfile: SLog.SLog = None, report_message_id: int = None):
        userslist = registered_users()
        random.shuffle(userslist)
        seslist = []
        for user in userslist:
            seslist.append(autoup_user(user, postlist.copy(), logfile=logfile))
        for i in seslist:
            i.start()
            time.sleep(random.randint(8, 30))
        for i in seslist:
            i.join()
        for peer in checking_peers():
            send_message(peer, 'Кажется, автоап окончен. Поглядите на результат.', None, None, None)
        if self.logfile!=None:
            self.logfile.add_string('Автоап окончен')