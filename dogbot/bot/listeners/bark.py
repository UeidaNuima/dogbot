from dogbot.cqsdk.utils import reply
import random


def bark(bot, message):
    if '汪' in message.text:
        reply(bot, message, random.choice([
            "汪!",
            "汪汪!",
            "汪汪汪!",
            "嗷？",
            "呜~",
            "poi!",
            "っぽい！",
            "ワン!",
            "わん!",
            "ワンワンワン",
            "poi?"
        ]))
    return False
