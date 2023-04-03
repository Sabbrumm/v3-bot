from modules.config import Config
from modules.databases import get_data, update_data, add_data, get_table_names, remove_data
from modules.v3except import V3Exception
from modules.apifuncs import getname
from vodka3S.supported_clients import VK_OFFICIAL
import vk_api
class User():
    def __init__(self, user_id):
        try:
            self._data = get_data('*', 'users', f'user_id={user_id}')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string':str(error),
                                                               'user_id':user_id})
        if self._data == []:
            raise V3Exception(V3Exception.USER_NOT_IN_DB, {'user_id':user_id})
        else:
            self._data = self._data[0]

            self.user_id = self._data[0]
            self.name = self._data[1]
            self.status = self._data[2]
            if self.status == 'fake':
                try:
                    self._fakedata = get_data('owner_id', 'fakes', f'fake_id={user_id}')
                    if self._fakedata==[]:
                        self.owner_id = None
                    else:
                        self.owner_id = self._fakedata[0][0]
                except Exception as error:
                    raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                                       'user_id': user_id})
            self.token = self._data[3]
            self.default_posts = self._data[4]
            self.referal_posts = self._data[5]
            self.do_likes = self._data[6]
            self.have_likes = self._data[7]
            self.sub_until = self._data[8]
            #self.thematic = self._data[9]

            self.summar_posts = self.default_posts+self.referal_posts
            self.vk_session = vk_api.VkApi(token=self.token,
                                           api_version='5.131',
                                           app_id=VK_OFFICIAL.client_id,
                                           client_secret=VK_OFFICIAL.client_secret)
            self.vk_session.http.headers['User-agent'] = VK_OFFICIAL.user_agent
    def update(self):
        column_names = get_table_names('users')
        selfdict = self.__dict__

        changes = []

        for key in selfdict:
            if key in column_names:
                val = selfdict[key]
                if isinstance(val, int):
                    changes.append(f"{key} = {val}")
                if isinstance(val, str):
                    changes.append(key+ '=' + '"' + val + '"')
                if str(type(val)) == "<class 'NoneType'>":
                    changes.append(f"{key} = Null")
        changes = ', '.join(changes)
        try:
            update_data("Users", changes,
                        f"user_id = {self.user_id}")
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'user_id': self.user_id})
    def move_to_archive(self):
        changes = [self.user_id, self.name, self.status, self.token,
                   self.default_posts, self.referal_posts, self.do_likes,
                   self.have_likes, self.sub_until, 0]
        try:
            if self.status != 'fake':
                add_data("Users_archive", changes)
                remove_data("Users", f'user_id = {self.user_id}')
            else:
                remove_data("Users", f'user_id = {self.user_id}')
                remove_data("Fakes", f'fake_id = {self.user_id}')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'user_id': self.user_id})
class ArchivedUser:
    def __init__(self, user_id):
        try:
            self._data = get_data('*', 'users_archive', f'user_id={user_id}')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string':str(error),
                                                               'user_id':user_id})
        if self._data == []:
            raise V3Exception(V3Exception.USER_NOT_IN_DB, {'user_id':user_id})
        else:
            self._data = self._data[0]

            self.user_id = self._data[0]
            self.name = self._data[1]
            self.status = self._data[2]
            if self.status == 'fake':
                try:
                    self._fakedata = get_data('owner_id', 'fakes', f'fake_id={user_id}')
                    if self._fakedata==[]:
                        self.owner_id = None
                    else:
                        self.owner_id = self._fakedata[0][0]
                except Exception as error:
                    raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                                       'user_id': user_id})
            self.token = self._data[3]
            self.default_posts = self._data[4]
            self.referal_posts = self._data[5]
            self.do_likes = self._data[6]
            self.have_likes = self._data[7]
            self.sub_until = self._data[8]
            #self.thematic = self._data[9]

            self.summar_posts = self.default_posts+self.referal_posts
            self.vk_session = vk_api.VkApi(token=self.token,
                                           api_version='5.131',
                                           app_id=VK_OFFICIAL.client_id,
                                           client_secret=VK_OFFICIAL.client_secret)
            self.vk_session.http.headers['User-agent'] = VK_OFFICIAL.user_agent
    def restore_from_archive(self):
        changes = [self.user_id, self.name, self.status, self.token,
                   self.default_posts, self.referal_posts, self.do_likes,
                   self.have_likes, self.sub_until, 0]
        try:
            add_data("Users", changes)
            remove_data("Users_archive", f'user_id = {self.user_id}')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'user_id': self.user_id})
class Post():
    def __init__(self, owner_id, post_id):
        try:
            self._data = get_data('*', 'posts', f'(owner_id={owner_id}) and (post_id={post_id})')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'post': (owner_id, post_id)})
        if self._data == []:
            raise V3Exception(V3Exception.POST_NOT_IN_DB, {'post': (owner_id, post_id)})
        else:
            self._data = self._data[0]

            self.owner_id = self._data[0]
            self.post_id = self._data[1]
            self.status = self._data[2]
            self.offered_by = self._data[3]
            self.like = self._data[4]
            self.wall_id = f'wall{owner_id}_{post_id}'
            self.status_ru = 'предложен'
            if self.status == 'approved':
                self.status_ru = 'проверен'
            if self.status == 'boosted':
                self.status_ru = 'в бусте'

    def update(self):
        column_names = get_table_names('posts')
        selfdict = self.__dict__

        changes = []

        for key in selfdict:
            if key in column_names:
                val = selfdict[key]
                if isinstance(val, int):
                    changes.append(f"{key} = {val}")
                if isinstance(val, str):
                    changes.append(key+ '=' + '"' + val + '"')
                if str(type(val)) == "<class 'NoneType'>":
                    changes.append(f"{key} = Null")
        changes = ', '.join(changes)
        try:
            update_data("Posts", changes,
                        f'(owner_id={self.owner_id}) and (post_id={self.post_id})')
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'post': (self.owner_id, self.post_id)})
class NewUser():
    def __init__(self, user_id, is_fake):
        self._is_fake = is_fake

        self.user_id = user_id
        self.name = getname(self.user_id)
        self.status = 'basic'
        if self._is_fake:
            self.status = 'fake'
            self.owner_id = None
        self.token = None
        self.default_posts = Config().new_user_posts
        self.referal_posts = 0
        self.do_likes = 1
        self.have_likes = 1
        self.sub_until = None
        #self.thematic = None
    def insert(self):
        changes = [self.user_id, self.name, self.status, self.token,
                   self.default_posts, self.referal_posts, self.do_likes,
                   self.have_likes, self.sub_until, 0]
        try:
            add_data("Users", changes)
            if self._is_fake:
                add_data("Fakes", [self.user_id, self.owner_id])
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'user_id': self.user_id})
class NewPost():
    def __init__(self, owner_id, post_id):
        self.owner_id = owner_id
        self.post_id = post_id
        self.status = 'suggested'
        self.offered_by = None
        self.like = 1
        self.wall_id = f'wall{owner_id}_{post_id}'
    def insert(self):
        changes = [self.owner_id, self.post_id, self.status, self.offered_by, self.like]
        try:
            add_data("Posts", changes)
        except Exception as error:
            raise V3Exception(V3Exception.DATABASE_EXCEPTION, {'error_string': str(error),
                                                               'post': (self.owner_id, self.post_id)})
