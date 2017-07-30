from dogbot.bot import bot
from dogbot.web import app
from mongoengine import connect
from config import config
import getopt
import sys
import threading
from importlib import reload
reload(threading)


def bot_main():
    print("QQBot is running...")
    try:
        bot.start()
    except KeyboardInterrupt:
        pass
    finally:
        print('Bye')


def web_main():
    app.run(host='0.0.0.0', threaded=True)

if __name__ == '__main__':
    connect(config.get('db'))
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'bw')
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    for o, a in opts:
        if o == '-b':
            bot_main()
        elif o in '-w':
            reload(threading)
            web_main()
        else:
            assert False, "unhandled option"

