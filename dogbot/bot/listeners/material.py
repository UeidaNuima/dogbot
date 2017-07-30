import getopt
import shlex

from config import config
from dogbot.cqsdk.utils import reply
from dogbot.models import *


def material(bot, message):
    """用法: -material [-h] [-r [-o]] 职业

    -h   : 打印本帮助
    -r   : 逆查
    -o   : 珠子逆查
    职业 : 职业名, 可以是日文原文或者黑话. 原文一概采用未cc的初始职业名. 也接受单位的日文原文或者黑话.

    例:
        -matrial 士兵
        -matrial -r 月影
        -matrial -r -o アルケミスト
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'material':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hro')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, material.__doc__)
        return True

    # 拆参数

    is_reverse = False
    is_orb = False

    for o, a in options:
        if o == '-r':
            # 反查
            is_reverse = True
        elif o == '-o':
            # 珠子反查
            is_orb = True
        elif o == '-h':
            # 帮助
            reply(bot, message, material.__doc__)
            return True

    # 必须要有职业参数
    if len(args) < 1:
        reply(bot, message, material.__doc__)
        return True

    target_name = args[0]

    target = Class.objects(Q(name=target_name) | Q(translate=target_name) | Q(nickname=target_name)).first()

    if not target:
        target = Unit.objects(Q(name=target_name) | Q(nickname=target_name)).first()
        if target:
            target = target.class_

    if not target:
        reply(bot, message, '没找到这个职业/单位...')
        return True

    msg = '{}({}):\n'.format(target.name, target.translate)
    if not is_reverse:
        # 查询素材

        if target.cc_material:
            msg += '\nCC素材: '
            for mat in target.cc_material:
                msg += '[{}] '.format(mat.translate)
        else:
            msg += '\n该职业没有CC'
        if target.awake_material:
            msg += '\n觉醒素材: '
            for mat in target.awake_material:
                msg += '[{}] '.format(mat.translate)

            msg += '\n珠子: '
            for mat in target.awake_orb:
                msg += '({}) '.format(mat.translate)
        else:
            msg += '\n该职业没有觉醒'

    else:
        # 反查
        if not is_orb:
            cc_usage = Class.objects(cc_material=target)
            if cc_usage:
                msg += '\nCC所用: '
                for usage in cc_usage:
                    msg += '[{}] '.format(usage.translate)
            else:
                msg += '\n该职业不会被CC所使用'

            awake_usage = Class.objects(awake_material=target)
            if awake_usage:
                msg += '\n觉醒所用: '
                for usage in awake_usage:
                    msg += '[{}] '.format(usage.translate)
            else:
                msg += '\n该职业不会被觉醒所使用'
        else:
            orb_usage = Class.objects(awake_orb=target)
            if orb_usage:
                msg += '\n珠子所用: '
                for usage in orb_usage:
                    msg += '[{}] '.format(usage.translate)
            else:
                msg += '\n该职业并不是珠子'

    reply(bot, message, msg)
    return True
