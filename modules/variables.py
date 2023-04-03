from modules.databases import sql_mode
from modules.config import Config
from modules.classes import Post, User
class LISTS:
    """Просто класс с простым вызовом запросов sql"""
    LIST_ALL = 'select user_id from users'
    LIST_BASICS = 'select user_id from users where status = "basic"'
    LIST_PREMIUMS = 'select user_id from users where status = "premium"'
    LIST_REFERALS = 'select user_id from users where status = "reseller"'
    LIST_HELPERS = 'select user_id from users where status = "helper"'
    LIST_ADMINS = 'select user_id from users where status = "admin"'
    LIST_STAFF = 'select user_id from users where (status = "helper") or (status = "admin")'
    LIST_FAKES = 'select user_id from users where (status = "fake")'
    LIST_SUBBED = 'select user_id from users where (sub_until is not NULL)'
    LIST_REGISTERED = 'select user_id from users where (token is not NULL)'
    LIST_UNREGISTERED = 'select user_id from users where (token is NULL)'
    def LIST_USER_FAKE_IDS(user_id):
        return f'select fake_id from fakes where (owner_id = {user_id})'
    LIST_SUGGESTED_POSTS = 'select owner_id, post_id from posts where status = "suggested"'
    LIST_APPROVED_POSTS = 'select owner_id, post_id from posts where status = "approved"'
    LIST_ALL_POSTS = 'select owner_id, post_id from posts where status != "boosted"'
    def LIST_USER_POSTS(user_id):
        return f'select owner_id, post_id from posts where (offered_by = {user_id})'

def all_ids():
    output = []
    for row in sql_mode(LISTS.LIST_ALL):
        output.append(row[0])
    return output
def basic_ids():
    output = []
    for row in sql_mode(LISTS.LIST_BASICS):
        output.append(row[0])
    return output
def premium_ids():
    output = []
    for row in sql_mode(LISTS.LIST_PREMIUMS):
        output.append(row[0])
    return output
def referal_ids():
    output = []
    for row in sql_mode(LISTS.LIST_REFERALS):
        output.append(row[0])
    return output
def helper_ids():
    output = []
    for row in sql_mode(LISTS.LIST_HELPERS):
        output.append(row[0])
    return output
def admin_ids():
    output = []
    for row in sql_mode(LISTS.LIST_ADMINS):
        output.append(row[0])
    return output
def fake_ids():
    output = []
    for row in sql_mode(LISTS.LIST_FAKES):
        output.append(row[0])
    return output
def staff_ids():
    output = []
    for row in sql_mode(LISTS.LIST_STAFF):
        output.append(row[0])
    return output
def subbed_ids():
    output = []
    for row in sql_mode(LISTS.LIST_SUBBED):
        output.append(row[0])
    return output
def registered_ids():
    output = []
    for row in sql_mode(LISTS.LIST_REGISTERED):
        output.append(row[0])
    return output

def bylist_ids(list):
    output = []
    for row in sql_mode(list):
        output.append(row[0])
    return output


def all_users():
    return [User(i) for i in all_ids()]
def basic_users():
    return [User(i) for i in basic_ids()]
def premium_users():
    return [User(i) for i in premium_ids()]
def referal_users():
    return [User(i) for i in referal_ids()]
def helper_users():
    return [User(i) for i in helper_ids()]
def admin_users():
    return [User(i) for i in admin_ids()]
def fake_users():
    return [User(i) for i in fake_ids()]
def staff_users():
    return [User(i) for i in staff_ids()]
def subbed_users():
    return [User(i) for i in subbed_ids()]
def registered_users():
    return [User(i) for i in registered_ids()]

def bylist_users(list):
    return [User(i) for i in bylist_ids(list)]

def get_user_fake_ids(user_id):
    output = []
    for row in sql_mode(LISTS.LIST_USER_FAKE_IDS(user_id)):
        output.append(row[0])
    return output
def get_user_fake_users(user_id):
    return [User(i) for i in get_user_fake_ids(user_id)]

def approved_posts():
    output = []
    for row in sql_mode(LISTS.LIST_APPROVED_POSTS):
        output.append(Post(row[0], row[1]))
    return output
def suggested_posts():
    output = []
    for row in sql_mode(LISTS.LIST_SUGGESTED_POSTS):
        output.append(Post(row[0], row[1]))
    return output
def need_to_check_posts():
    srez = Config().max_posts_per_boost-len(approved_posts())
    print(suggested_posts())
    output = suggested_posts()[:srez]
    return output

def all_posts():
    output = []
    for row in sql_mode(LISTS.LIST_ALL_POSTS):
        print(row)
        output.append(Post(row[0], row[1]))
    return output

def wall_ids_list(postlist):
    return [i.wall_id for i in postlist]

def get_user_posts(user_id):
    output = []
    for row in sql_mode(LISTS.LIST_USER_POSTS(user_id)):
        output.append(Post(row[0], row[1]))
    return output

def get_bot_name():
    return f"{Config().bot_name} ({Config().bot_dev_name})"

def checking_peers():
    return Config().checking_peers
def main_peers():
    return Config().main_peers

def boost_enabled():
    return Config().global_boost

def autoups_enabled():
    return Config().global_ups

def autolikes_enabled():
    return Config().global_likes

def get_fake_owner(fake_id):
    us = User(fake_id)
    return us.owner_id if us.owner_id!=None else -1*Config().group_id

def get_alert_text():
    return None


def set_approved_boosted():
    sql_mode('update posts set status = "boosted" where status = "approved"')

def clear_boosted():
    sql_mode('delete from posts where status = "boosted"')

def clear_approved():
    sql_mode('delete from posts where status = "approved"')

def clear_specific(owner_id, post_id):
    sql_mode(f'delete from posts where (owner_id = {owner_id}) and (post_id={post_id})')

def clear_fake(fake_id):
    sql_mode(f'delete from fakes where fake_id = {fake_id}; delete from users where user_id = fake_id')

def clear_posts_from_user(user_id):
    sql_mode(f'delete from posts where offered_by = {user_id}')