from dogbot.bot import bot
from mongoengine import connect


if __name__ == '__main__':
    connect()
    print("QQBot is running...")
    try:
        bot.start()
    except KeyboardInterrupt:
        pass
    finally:
        print('Bye')

