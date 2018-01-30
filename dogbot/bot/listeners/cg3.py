from config import config
from dogbot.cqsdk.utils import reply
from dogbot.models import Unit, UnitUnpack
from mongoengine import Q
import shlex


def cg3(bot, message):
    """#cg3 [单位]"""
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'cg3':
        return False

    if args:
        target_name = args[0]
        target = Unit.objects(Q(name=target_name) | Q(nickname=target_name)).first()
        if not target:
            reply(bot, message, '找不到单位{}...'.format(target_name))
            return True
        target = UnitUnpack.objects(Name=target.name).first()
        if target.has_cg3():
            reply(bot, message, '{}, 有cg3'.format(target.Name))
        else:
            reply(bot, message, '{}, 没有cg3'.format(target.Name))
    else:
        targets = UnitUnpack.objects().all()
        cg3s = [[], [], [], [], [], [], [], []]
        for target in targets:
            if target.has_cg3():
                cg3s[target.Rare].append(target.Name)
        reply(bot, message, '金：\n{0[3]}\n白：\n{0[4]}\n黑：\n{0[5]}\n蓝：\n{0[7]}'.format(list(map(lambda names: ', '.join(names), cg3s))))
        return True
    return True
