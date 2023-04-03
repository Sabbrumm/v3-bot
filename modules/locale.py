import configparser
from paths import LOCALE_PATH

class RESP:
    def __init__(self, CP):
        self.CP = CP

    @property
    def GET_RULES(self):
        return self.CP['Responses']['GET_RULES']

    @property
    def NO_RIGHTS(self):
        return self.CP['Responses']['NO_RIGHTS']

    def WELCOME_NEW(self, full_name):
        return self.CP['Responses']['WELCOME_NEW'].format(full_name = full_name)

class LOC:
    CP = configparser.ConfigParser()
    CP.read_file(open(LOCALE_PATH, 'r', encoding="utf8"))
    RESPONSES = RESP(CP)


LOCALE = LOC()
