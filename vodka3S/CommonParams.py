from .supported_clients import VK_OFFICIAL
import random


class CommonParams:
    def __init__(self, vk_ua=None, gcm_ua=None):
        if vk_ua is None:
            self._vk_ua = VK_OFFICIAL.user_agent
        else:
            self._vk_ua = vk_ua

        if gcm_ua is None:
            self._gcm_ua = 'Android-GCM/1.5 (generic_x86 KK)'
        else:
            self._gcm_ua = gcm_ua

    def get_two_factor_part(self, code=None):
        if code is None:
            return []
        return [
                   ('2fa_supported', 1),
                   ('force_sms', 1)
               ] + [] if code == 'GET_CODE' else [('code', code)]
    def get_captcha_part(self, captcha_sid=None, captcha_key=None):
        if captcha_sid == None or captcha_key == None:
            return []
        return [
                   ('captcha_sid', captcha_sid),
                   ('captcha_key', captcha_key)
               ]

    def generate_random_string(self, length, characters):
        return ''.join(random.choice(characters) for _ in range(length))

    def set_common_vk(self, session):
        session.headers.update({'User-Agent': self._vk_ua})

    def set_common_gcm(self, session):
        session.headers.update({'User-Agent': self._gcm_ua})
