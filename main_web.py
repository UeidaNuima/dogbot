from dogbot.web import app
from mongoengine import connect
from config import config


if __name__ == '__main__':
    connect(config.get('db'))
    app.run(host='0.0.0.0', threaded=True)
