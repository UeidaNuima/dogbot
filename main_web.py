from dogbot.web import app
from mongoengine import connect
from config import config

connect(config.get('bot_db'), alias="bot")

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
