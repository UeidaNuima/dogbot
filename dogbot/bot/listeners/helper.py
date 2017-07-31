from dogbot.cqsdk.utils import reply
import getopt
from config import config
import shlex
from dogbot.models import *


def alias_command(bot, message):
    """#alias [-h] [-d 原命令] [命令]

    -h       : 打印本帮助
    -d 命令   : 要操作的命令
    命令      : 命令的别名

    例:
        #alias -d #conne 圆爹 (然后就可以使用 圆爹 狗蛋 的语法了)
        #alias (输出所有的alias)
        #alias 圆爹 (输出"圆爹"对应的原命令)
    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'alias':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hd:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, alias_command.__doc__)
        return True

    origin = None

    for o, a in options:
        if o == '-d':
            origin = a
        elif o == '-h':
            # 帮助
            reply(bot, message, alias_command.__doc__)
            return True

    # 没有命令, 列出全部别名
    if not args:
        # 列出所有名字
        alias = Alias.objects()
        aliases = []
        for a in alias:
            aliases.append('{} => {}'.format(a.alias, a.origin))
        msg = '{}'.format('\n'.join(aliases))
        reply(bot, message, msg)
        return True

    command = args[0]
    alias = Alias.objects(alias=command)

    # 没有原命令, 输出该命令的别名
    if not origin:
        if not alias:
            reply(bot, message, '没找到别名{}'.format(command))
            return True
        msg = '{} => {}'.format(alias.alias, alias.origin)
        reply(bot, message, msg)
        return True

    # 都有但是alias存在了, 报错
    if alias:
        reply(bot, message, '{}已经存在'.format(command))
        return True

    alias = Alias(origin=origin, alias=command)
    alias.save()

    reply(bot, message, '{} => {}'.format(alias.alias, alias.origin))
    return True


def unalias_command(bot, message):
    """#unalias [-h] 命令

    -h  : 打印本帮助
    命令 : 要删除的别名
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'unalias':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hd:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, unalias_command.__doc__)
        return True

    origin = None

    for o, a in options:
        if o == '-h':
            # 帮助
            reply(bot, message, unalias_command.__doc__)
            return True

    # 一定要有命令
    if not args:
        reply(bot, message, unalias_command.__doc__)
        return True

    command = args[0]
    alias = Alias.objects(alias=command)

    if not alias:
        reply(bot, message, '没找到别名{}'.format(command))

    reply(bot, message, '删掉了别名 {} => {}'.format(alias.alias, alias.origin))
    alias.delete()
    return True


def alias_parser(bot, message):
    """处理别名命令"""
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        cmd = message.text
    alias = Alias.objects(alias=cmd).first()
    if alias:
        text = message.text.replace(cmd, alias.origin, 1)
        return message._replace(text=text)
    else:
        return False


def help(bot, message):
    """#help

    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'help':
        return False
    msg = ['ケルベロス ver3.0']
    msg_help = []
    for listener in bot.listeners:
        if listener.handler.__doc__ and listener.handler.__doc__[0] == config['splitter']:
            msg_help.append(listener.handler.__doc__.split('\n')[0])
    # 给命令排个序
    msg.extend(sorted(msg_help))
    msg.append('-----')
    for alias in Alias.objects:
        msg.append('{} => {}'.format(alias.alias, alias.origin))
    msg.append('-----')
    msg.append(config.get('extra_comments'))
    reply(bot, message, '\n'.join(msg))
    return True


