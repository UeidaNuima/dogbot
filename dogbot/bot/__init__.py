from dogbot.cqsdk import CQBot, RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage
from mongoengine import connect
from config import config

# connect('aigis')

bot = CQBot(11235, 12450, debug=config.get('debug', False))

# bark!
from dogbot.bot.listeners.bark import bark
bot.add_listener(bark, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# helper
from dogbot.bot.listeners.helper import alias_command, unalias_command, alias_parser, help
bot.add_listener(alias_parser, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(help, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(unalias_command, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(alias_command, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# roll
from dogbot.bot.listeners.roll import roll
bot.add_listener(roll, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 喂桶
from dogbot.bot.listeners.bucket import bucket
bot.add_listener(bucket, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 素材
from dogbot.bot.listeners.material import material
bot.add_listener(material, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 计算器
from dogbot.bot.listeners.calc import calc
bot.add_listener(calc, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 属性图与圆爹图
from dogbot.bot.listeners.unit import status, conne
bot.add_listener(status, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(conne, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# emoji
from dogbot.bot.listeners.emoji import emoji_base, emoji_del, emoji_alias, emoji_parser, emoji_lock
bot.add_listener(emoji_parser, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(emoji_alias, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(emoji_del, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(emoji_base, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))
bot.add_listener(emoji_lock, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 海报
from dogbot.bot.listeners.poster import poster
bot.add_listener(poster, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# twitter
from dogbot.bot.listeners.twitter import twitter
bot.add_listener(twitter, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# group_ban
from  dogbot.bot.listeners.group_ban import group_ban
bot.add_listener(group_ban, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# 搞死你們網頁鏈接人
from dogbot.bot.listeners.gbf import gbf
bot.add_listener(gbf, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage))

# twitter定时任务
from dogbot.bot.twitter import poll_twitter
bot.scheduler.add_job(poll_twitter, 'interval', args=(bot, ), seconds=30, max_instances=10)
