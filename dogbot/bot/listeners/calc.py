import re
import shlex

from config import config
from dogbot.cqsdk.utils import reply


def calc(bot, message):
    """#calc 表达式

    表达式 : 算数表达式, 支持+-*/^(). 其他符号全部都会被escape掉. 可以有空格. 小数会被保留5位.

    例:
        #calc 810+931-114514-1919
    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'calc':
        return False

    args = ''.join(args)
    match = re.match('[0-9\(\)\+\-\*\/\^\&\%\|\.\~\<\> ]+', args)
    if match:
        try:
            reply(bot, message, str(round(eval(match.group(0).replace('^', '**')), 5)))
        except:
            reply(bot, message, '格式不对...')
    return True
