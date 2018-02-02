from dogbot.web import app
from mongoengine import connect
from config import config


if __name__ == '__main__':
    connect(config.get('bot_db'), alias="bot")
    app.run(host='0.0.0.0', threaded=True)
