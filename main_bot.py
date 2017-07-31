from dogbot.bot import bot
from mongoengine import connect
from config import config


if __name__ == '__main__':
    connect(config.get('db'))
    print("QQBot is running...")
    try:
        bot.start()
    except KeyboardInterrupt:
        pass
    finally:
        print('Bye')

