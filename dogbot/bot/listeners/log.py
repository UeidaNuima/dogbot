from dogbot.models import *
from dogbot.bot.cqsdk import RcvdGroupMessage, RcvdPrivateMessage, RcvdDiscussMessage


def log(bot, message):
    """
    记录聊天记录.
    """
    logging = Log(qq=message.qq, type=type(message).__name__)

    if isinstance(message, RcvdGroupMessage):
        logging.group = message.group

    elif isinstance(message, RcvdDiscussMessage):
        logging.discuss = message.discuss

    logging.save()
    return False
