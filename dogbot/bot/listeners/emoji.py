import getopt
import random
import re
import shlex
from configparser import ConfigParser

import requests
from dogbot.cqsdk import CQImage, RcvdGroupMessage
from mongoengine import connect

from dogbot.cqsdk.utils import reply
from dogbot.models import *


def emoji_base(bot, message):
    """#emoji [-h] [-d 名称] [内容...]

    -h     : 打印本帮助
    -d 名称 : emoji的名称
    内容    : 要录入的内容, 可以有图片也可以有文字, 也可以是混合内容. 一个名称可以有多个内容. 当没有内容时将输出列表.

    例:
        #emoji -d 班长 班长!!!.jpg
        #emoji -d 我好菜啊 你是坏菜!
        #emoji  (将列出所有emoji列表)
        #emoji -d 班长  (将列出班长emoji的列表)
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'emoji':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hd:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, emoji_base.__doc__)
        return True

    name = None

    for o, a in options:
        if o == '-d':
            name = a
        elif o == '-h':
            # 帮助
            reply(bot, message, emoji_base.__doc__)
            return True

    # 没有内容的时候输出列表
    if not name:
        # 列出所有名字
        emojis = Emoji.objects()
        names = []
        for emoji in emojis:
            names.append('[' + ','.join(emoji.name) + ']')
        msg = '现在保存了以下内容: \n{}' .format(';'.join(names))
        reply(bot, message, msg)
        return True
    if not args:
        # 列出当前名字下的所有表情
        emoji = Emoji.objects(name=name).first()
        if not emoji:
            reply(bot, message, '没找到名字{}'.format(name))
            return True
        msg = '{}对应以下内容: \n'.format(emoji.name)
        msg_emojis = []
        for index, content in enumerate(emoji.emoji):
            msg_emojis.append('[{}] => [{}]'.format(index + 1, content))
        msg += ';'.join(msg_emojis)
        reply(bot, message, msg)
        return True

    # 内容
    content = ' '.join(args)

    # 有内容, 是增加
    emoji = Emoji.objects(name=name).first()
    if not emoji:
        emoji = Emoji()
        emoji.name.append(name)

    # 找图片
    files = CQImage.PATTERN.findall(content)
    # 遍历
    for filename in files:
        dir = os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'emoji')
        path = os.path.join(dir, filename)
        if not os.path.exists(dir):
            os.mkdir(dir)
        cqimg = os.path.join(config['cq_root_dir'], config['cq_image_dir'], filename + '.cqimg')
        parser = ConfigParser()
        parser.read(cqimg)
        url = parser['image']['url']
        r = requests.get(url, timeout=30, proxies=config.get('proxies', {}))
        # 下载
        if r.status_code > 200:
            reply(bot, message, '下挂了...网络问题？')
            return True
        with open(path, 'wb') as f:
            f.write(r.content)

    content = CQImage.PATTERN.sub(str(CQImage('emoji/\\1')), content)
    emoji.emoji.append(content)
    emoji.save()

    if len(emoji.emoji) > 10:
        msg = '[{}]现在含有{}个emoji'.format(','.join(emoji.name),str(len(emoji.emoji)))
    else:
        msg = '[{}]现在对应以下内容: \n{}'.format(','.join(emoji.name), '[' + '];['.join(emoji.emoji) + ']')
    reply(bot, message, msg)


def emoji_del(bot, message):
    """#emoji_del [-h] [-s 索引] 名字

    -h     : 打印本帮助
    -s 索引 : 删除单个emoji. 索引从1开始, 可以用emoji_list命令获取具体索引.
    名称    : emoji的名称.

    例:
        #emoji_del 班长 (将会把emoji班长删掉)
        #emoji_del -s 2 班长 (将会把班长emoji的第二张图删掉, 前提是班长emoji里至少有两张图)
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'emoji_del':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hs:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, emoji_del.__doc__)
        return True

    index = None

    for o, a in options:
        if o == '-s':
            index = a
            try:
                index = int(index)
                if index <= 0:
                    raise ValueError
            except ValueError:
                reply(bot, message, '索引应该是正整数')
                return True
        elif o == '-h':
            # 帮助
            reply(bot, message, emoji_del.__doc__)
            return True

    if len(args) < 1:
        reply(bot, message, '没输入名称...')
        return True

    emoji = Emoji.objects(name=args[0]).first()

    if not emoji:
        reply(bot, message, '没找到{}...'.format(args[0]))
        return True

    if not index:
        reply(bot, message, '删掉了[{}]'.format(','.join(emoji.name)))
        emoji.delete()
        return True
    else:
        index -= 1
        if len(emoji.emoji) > index:
            if len(emoji.emoji) == 1:
                reply(bot, message, '名称{}只含有一个emoji了, 如果想要删除该emoji请使用emoji_del命令直接删除'.format(emoji.name))
                return True
            del emoji.emoji[index]
            emoji.save()
            reply(bot, message, '删掉了[{}]的第{}个emoji'.format(','.join(emoji.name), index + 1))
        else:
            reply(bot, message, '索引越界')
        return True


def emoji_alias(bot, message):
    """#emoji_alias [-h] [-r] [-d 名称] [名称]

    -h      : 打印本帮助
    -r      : 删除名称
    -d 名称 : 要操作的emoji的名称
    名称    : 增加的emoji的名称

    例:
        #emoji_alias -d 班长 班长!! (班长!!将也会成为班长emoji的名称)
        #emoji_alias -r -d 班长 (班长将会从班长emoji中删除)
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'emoji_alias':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hrd:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, emoji_alias.__doc__)
        return True

    name = None
    delete = False

    for o, a in options:
        if o == '-d':
            name = a
        elif o == '-r':
            delete = True
        elif o == '-h':
            # 帮助
            reply(bot, message, emoji_alias.__doc__)
            return True

    if not name:
        reply(bot, message, emoji_alias.__doc__)
        return True

    emoji = Emoji.objects(name=name).first()
    if not emoji:
        reply(bot, message, '找不到名称{}'.format(name))
        return True

    if delete:
        if len(emoji.name) == 1:
            reply(bot, message, '名称{}只含有一个名称了, 如果想要删除该emoji请使用emoji_del命令'.format(name))
            return True
        index = emoji.name.index(name)
        del emoji.name[index]
        emoji.save()
        reply(bot, message, '删掉了名称{}'.format(name))
        return True
    else:
        if not args:
            reply(bot, message, emoji_alias.__doc__)
            return True
        name_add = args[0]
        emoji.name.append(name_add)
        emoji.save()
        reply(bot, message, '{}也是{}的名称了!'.format(name_add, name))
        return True


EMOJI_PATTERN = re.compile('[\(（](.*?)[\)）]')


def replacer(matchobj):
    sub = Emoji.objects(name=matchobj.group(1)).first()
    if sub:
        return random.choice(sub.emoji)
    else:
        return matchobj.group(0)


def emoji_parser(bot, message):
    if EMOJI_PATTERN.search(message.text):
        try:
            if message.text.split()[0] == '/calc':
                return False
        except IndexError:
            pass
        res = EMOJI_PATTERN.sub(replacer, message.text)
        if not res == message.text:
            reply(bot, message, res)
            return True
    emoji = Emoji.objects(name=message.text).first()
    if emoji:
        reply(bot, message, random.choice(emoji.emoji))
        return True

    return False


if __name__ == '__main__':
    connect('aigis')
    emoji_base([], RcvdGroupMessage(qq=123, group=333, text='-emoji_add -d aaa [CQ:image,file=123.jpg]a[CQ:image,file=asdf.png]'))
