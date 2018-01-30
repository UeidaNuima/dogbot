from dogbot.bot import bot
from mongoengine import connect
from config import config


if __name__ == '__main__':
    connect(config.get('bot_db'), alias="bot")
    connect(config.get('unpack_db'), alias="unpack")
    print("QQBot is running...")
    try:
        bot.start()
    except KeyboardInterrupt:
        pass
    finally:
        print('Bye')

