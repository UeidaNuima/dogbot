import random

from dogbot.cqsdk.utils import reply
from config import config
import shlex

ROLL_LOWER = 2
ROLL_UPPER = 7000
ROLL_SEPARATOR = ','
ROLL_HELP = "[roll] 有效范围为 {} ~ {}".format(ROLL_LOWER, ROLL_UPPER)


def roll(bot, message):
    """#roll

    例:
        #roll 4
        #roll 4,6,10
        #roll 5 10 200 a,b,c
    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd == config['splitter'] + 'roll':
        return False

    # texts = RE_CQ_SPECIAL.sub('', message.text).split()

    ranges = []
    for text in args:
        # /roll 100
        try:
            n = int(text)
            if ROLL_LOWER <= n <= ROLL_UPPER:
                ranges.append(n)
            else:
                reply(bot, message, ROLL_HELP)
                return True
            continue
        except ValueError:
            pass
        # /roll 1,20,100
        if ROLL_SEPARATOR in text:
            n = text.split(',')
            ranges.append(n)
            continue
        # else
        break
    if len(ranges) == 0:
        ranges = [100]

    rolls = []
    for n in ranges:
        if isinstance(n, int):
            rolls.append("{}/{}".format(random.randint(1, n), n))
        if isinstance(n, (list, tuple)):
            rolls.append("{}/{}".format(random.choice(n),
                                        ROLL_SEPARATOR.join(n)))
    roll_text = ", ".join(rolls)
    send_text = "[roll][CQ:at,qq={}]: {}".format(message.qq, roll_text)

    reply(bot, message, send_text)
    return True
