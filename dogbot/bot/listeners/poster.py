import os
import io
import shlex
from datetime import datetime, timedelta
import getopt
import requests
from dogbot.cqsdk import CQImage, RcvdPrivateMessage
from PIL import Image

from config import config
from dogbot.cqsdk.utils import reply

BASE_URL = 'http://s3-ap-northeast-1.amazonaws.com/assets.millennium-war.net/00/html/image/'


def poster(bot, message):
    """#poster [-h] [-f]

    -h : 打印本帮助
    -f : 强制刷新
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'poster':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hf')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, poster.__doc__)
        return True

    refresh = False

    # 拆参数
    for o, a in options:
        if o == '-h':
            # 帮助
            reply(bot, message, poster.__doc__)
            return True
        elif o == '-f':
            refresh = True

    weekday = datetime.now().weekday()
    if weekday >= 3:
        delta = timedelta(days=weekday-3)
    else:
        delta = timedelta(days=7+weekday-3)

    thu_date = datetime.now().date() - delta
    url = '{}event{}.jpg'.format(BASE_URL, thu_date.strftime('%Y%m%d'))
    filename = os.path.basename(url)
    dir = os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'poster')
    path = os.path.join(dir, filename)

    if not os.path.exists(dir):
        os.mkdir(dir)

    if not os.path.exists(path) or refresh:
        resp = requests.get(url, timeout=60, proxies=config.get('proxies'))
        if not resp.status_code == 200:
            reply(bot, message, '没找到海报...还没更新或者是网络问题?')
            return True
        # 压缩图片
        img = Image.open(io.BytesIO(resp.content))
        img.save(path, quality=40)
        # with open(path, 'wb') as f:
        #     f.write(resp.content)

    reply(bot, message, CQImage(os.path.join('poster', filename)))
    return True


if __name__ == '__main__':
    poster([], RcvdPrivateMessage(qq=123, text='#poster'))

