import time

from .supported_clients import VK_OFFICIAL
from .TokenException import TokenException
from .CommonParams import CommonParams
from .AndroidCheckin import AndroidCheckin
from .SmallProtobufHelper import SmallProtobufHelper
from .DefaultUserTalk import DefaultUserTalk
import requests
class TokenReceiver:
    def __init__(self, login=None, password=None, auth_code=None, user_talk=DefaultUserTalk(), params=CommonParams(), scope='all'):
        self._params = params
        self._login = login
        self._password = password
        self._auth_code = auth_code
        self._auth_data = AndroidCheckin(CommonParams(), SmallProtobufHelper()).do_checkin()
        self._scope = scope
        self._client = VK_OFFICIAL
        self._user_talk=user_talk
        self._session = requests.Session()
        self._params.set_common_vk(self._session)
    def get_token(self, non_refreshed_token=None):
        ret_d = {}
        receipt = self._get_receipt()
        if non_refreshed_token is None:
            data = self._get_non_refreshed()
            token = data['access_token']
            user_id = data['user_id']
            ret_d['base_token'] = token
            ret_d['user_id'] = user_id
        else:
            token = non_refreshed_token
            ret_d['base_token'] = token
        new_token = self._refresh_token(token, receipt)
        ret_d['refreshed_token'] = new_token
        return ret_d

    def _get_receipt(self):
        session = requests.Session()
        self._params.set_common_gcm(session)
        session.headers.update({
            'Authorization': 'AidLogin ' + self._auth_data['id'] + ':' + self._auth_data['token']
        })
        data = {
            "X-scope": "*",
            "X-subtype": "841415684880",
            "X-appid": self._params.generate_random_string(
                22,
                '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-'),
            "app": "com.vkontakte.android",
            "sender": "841415684880",
            "device": self._auth_data['id'],
            "X-X-kid": "|ID|1|"
        }
        result = session.post('https://android.clients.google.com/c2dm/register3', data=data).content.decode('ascii')
        try:
            receipt = result.split(':')[1]
        except:
            time.sleep(2)
            return self._get_receipt()
        if receipt == 'PHONE_REGISTRATION_ERROR':
            raise TokenException(TokenException.REGISTRATION_ERROR, result)
        return receipt

    def _get_non_refreshed(self):
        captcha_sid = None
        captcha_key = None
        valid_sid = None
        phone_mask = None
        while True:


            dec = self._session.get('https://oauth.vk.com/token',
                              params=[
                                         ('grant_type', 'password'),
                                         ('client_id', self._client.client_id),
                                         ('client_secret', self._client.client_secret),
                                         ('username', self._login),
                                         ('password', self._password),
                                         ('v', '5.131'),
                                         ('lang', 'en'),
                                         ('scope', self._scope)
                                     ]
                                     +
                                     self._params.get_two_factor_part(self._auth_code)
                                     +
                                     self._params.get_captcha_part(captcha_sid, captcha_key)
                              ).json()
            if 'error' in dec and dec['error'] == 'need_validation':
                if self._user_talk != None:
                    try:
                        valid_sid = dec['validation_sid']
                        phone_mask = dec['phone_mask']
                        self._auth_code = self._user_talk.handle_twofa(dec['validation_sid'], phone_mask=dec['phone_mask'])
                    except Exception as uu:
                        print(uu)
                        raise TokenException(TokenException.NO_ANSWER, {'error': 'reg_failed_wait'})
                    if self._auth_code==0:
                        raise TokenException(TokenException.STOPPED, {'error': 'reg_stopped'})
                    continue
                else:
                    raise TokenException(TokenException.TWOFA_REQ, dec)
            if 'error' in dec and dec['error'] == 'need_captcha':
                if self._user_talk!= None:
                    try:
                        captcha_sid, captcha_key = self._user_talk.handle_captcha(dec['captcha_sid'], dec['captcha_img'])
                    except:
                        raise TokenException(TokenException.NO_ANSWER, {'error': 'reg_failed_wait'})
                    if captcha_sid==captcha_key and captcha_key==0:
                        raise TokenException(TokenException.STOPPED, {'error': 'reg_stopped'})
                    continue
                else:
                    raise TokenException(TokenException.CAPTCHA_NEEDED, dec)
            if 'error' in dec and dec['error'] == 'invalid_request':
                if dec['error_type'] == 'otp_format_is_incorrect' or dec['error_type'] == 'wrong_otp':
                    if self._user_talk != None:
                        try:
                            self._auth_code = self._user_talk.handle_twofa(valid_sid, previous_wrong=1,
                                                                           phone_mask=phone_mask)
                        except Exception as uu:
                            print(uu)
                            raise TokenException(TokenException.NO_ANSWER, {'error': 'reg_failed_wait'})

                        continue
                    else:
                        raise TokenException(TokenException.TWOFA_REQ, dec)
            if 'user_id' not in dec:
                raise TokenException(TokenException.TOKEN_NOT_RECEIVED, dec)
            return {'access_token': dec['access_token'], 'user_id': dec['user_id']}

    def _refresh_token(self, token, receipt):
        session = requests.Session()
        self._params.set_common_vk(session)
        dec = session.get('https://api.vk.com/method/auth.refreshToken',
                          params=[
                              ('access_token', token),
                              ('receipt', receipt),
                              ('v', '5.95')
                          ]).json()
        new_token = dec['response']['token']
        if new_token == token:
            raise TokenException(TokenException.TOKEN_NOT_REFRESHED)
        return new_token
