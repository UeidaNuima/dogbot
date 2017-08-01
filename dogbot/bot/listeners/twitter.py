import getopt
import shlex
from datetime import datetime, timedelta
from config import config
from mongoengine import Q

from dogbot.cqsdk.utils import reply
from dogbot.models import Twitter


def twitter(bot, message):
    """#twitter [-p 天数]

    -p : 几天以前
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'twitter':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hp:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, twitter.__doc__)
        return True

    days = 0
    for o, a in options:
        if o == '-p':
            # 几天以前
            try:
                days = int(a)
                if days < 0:
                    raise ValueError
            except ValueError:
                reply(bot, message, twitter.__doc__)
                return True
        elif o == '-h':
            # 帮助
            reply(bot, message, twitter.__doc__)
            return True
    tweets = Twitter.objects(Q(date__gte=datetime.now().date()+timedelta(days=-days)) & Q(date__lte=datetime.now().date()+timedelta(days=-days+1)))

    if tweets:
        reply(bot, message, '\n---------\n'.join([str(tweet) for tweet in tweets]))
        return True
    else:
        reply(bot, message, '安娜啥都没说...')
        return True
