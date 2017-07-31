from dogbot.bot import bot


if __name__ == '__main__':
    print("QQBot is running...")
    try:
        bot.start()
    except KeyboardInterrupt:
        pass
    finally:
        print('Bye')

