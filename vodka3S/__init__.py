from .AndroidCheckin import AndroidCheckin
from .CommonParams import CommonParams
from .MTalkClient import MTalkClient
from .MTalkException import MTalkException
from .ProtobufException import ProtobufException
from .SmallProtobufHelper import SmallProtobufHelper
from .TokenException import TokenException
from .TokenReceiver import TokenReceiver
from .TwoFAHelper import TwoFAHelper
from .VkClient import VkClient
from .DefaultUserTalk import DefaultUserTalk
from . import supported_clients


def get_token(login, password, auth_code=None, user_talk = DefaultUserTalk()):
    """пример функции default user talk смотрите в библе"""
    receiver = TokenReceiver(login, password, auth_code, user_talk=user_talk)
    return receiver.get_token()


