from dogbot.cqsdk.utils import reply
from dogbot.cqsdk import GroupBan
from config import config
import shlex


def group_ban(bot, message):

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'group_ban':
        return False
    pass

    if message.qq not in config['admins']:
        return True

    group = int(args[0])
    qq = int(args[1])
    duration = int(args[2])
    bot.send(GroupBan(group=group, qq=qq, duration=duration))
    return True
