from mongoengine import *
import os
import requests
from config import config
from datetime import timezone, timedelta, datetime
from dogbot.cqsdk import CQImage
import threading
from importlib import reload
reload(threading)


class Exp(Document):
    lv = IntField(required=True)
    rarity = IntField(required=True)
    exp = IntField(required=True)


class Class(Document):
    name = StringField(required=True, unique=True)
    nickname = ListField(StringField())
    translate = StringField(required=True)
    cc_material = ListField(ReferenceField('self'))
    awake_material = ListField(ReferenceField('self'))
    awake_orb = ListField(ReferenceField('self'))


class Unit(Document):
    name = StringField(required=True)
    nickname = ListField(StringField())
    class_ = ReferenceField(Class, db_field='class')
    rarity = IntField()
    conne_name = StringField()


class Twitter(Document):
    id = StringField(required=True, primary_key=True)
    text = StringField(required=True)
    date = DateTimeField(required=True)
    media = ListField(StringField())

    def __str__(self):
        for url in self.media:
            filename = os.path.basename(url)
            dir = os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'twitter')
            path = os.path.join(dir, filename)
            # 没有twitter文件夹的话就新建一个
            if not os.path.exists(dir):
                os.mkdir(dir)
            # 下图
            if not os.path.exists(path):
                resp = requests.get(url, timeout=60, proxies=config.get('proxies'))
                with open(path, 'wb') as f:
                    f.write(resp.content)

        dt = self.date.astimezone(timezone(timedelta(hours=9)))
        ds = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S JST")
        results = [ds, ]
        text = self.text
        text = text.replace('・', '·').replace('✕', '×').replace('#千年戦争アイギス', '').replace('♪', '')
        results.extend(['', text.strip()])
        results.extend([str(CQImage(os.path.join('twitter', os.path.basename(m)))) for m in self.media])
        return '\n'.join(results)


class Emoji(Document):
    name = ListField(StringField(unique=True))
    emoji = ListField(StringField())


class Log(Document):
    time = DateTimeField(default=datetime.now(), required=True)
    qq = StringField(required=True)
    group = StringField()
    discuss = StringField()
    type_ = StringField(required=True, db_field='type')


class Alias(Document):
    origin = StringField(required=True)
    alias = StringField(required=True, unique=True)
