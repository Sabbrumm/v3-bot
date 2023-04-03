from .TwoFAHelper import TwoFAHelper
from .TokenException import TokenException
class DefaultUserTalk:
    def __init__(self):
        pass
    def handle_captcha(self, captcha_sid, captcha_link):
        # функция обработки капчи. обязательно должна выдавать на выходе captcha_sid, captcha_key
        captcha_key = input(f"Введите капчу с картинки {captcha_link} : ")
        if captcha_key == 'stop':
            return 0, 0
        return captcha_sid, captcha_key
    def handle_twofa(self, validation_sid, phone_mask='defaultphonemask', previous_wrong = 0):
        # функция обработки двухфакторки. обязательно должна выдавать на выходе twofa_code
        while 1:
            if not previous_wrong:
                twofa_code = input(f"Введите код двухфакторки или sms для высылки смс:")
                print('\n')
            else:
                twofa_code = input(f"Неверный код. Введите код двухфакторки или s для высылки смс:")
                print('\n')
            if twofa_code == 'sms':

                try:
                    TwoFAHelper().validate_phone(validation_sid)
                    print(f"СМС выслано на номер {phone_mask}")
                except TokenException as err:
                    err = err.extra
                    if 'error' in err and 'error_code' in err['error']:
                        if err['error']['error_code'] == 1112:
                            print("Подождите пару минут, код пока нельзя выслать")
                        if err['error']['error_code'] == 103:
                            print("Код уже был выслан. Проверьте свои сообщения")
                    else:
                        print("Невозможно выслать смс")
                continue
            if twofa_code == 'stop':
                return 0
            else:
                return twofa_code