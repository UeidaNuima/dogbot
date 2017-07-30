from config import config
import requests
from requests_oauthlib import OAuth1Session, OAuth1
from dogbot.models import Twitter
from datetime import datetime, timedelta, timezone
from mongoengine import connect
from dogbot.cqsdk import SendGroupMessage


auth = OAuth1(
    client_key=config['twitter']['client_key'],
    client_secret=config['twitter']['client_secret'],
    resource_owner_key=config['twitter']['resource_owner_key'],
    resource_owner_secret=config['twitter']['resource_owner_secret']
)

def exception_handler(request, exception):
    print('twitter', exception)


def poll_twitter(bot):
    resp = requests.get(
        url="https://api.twitter.com/1.1/statuses/user_timeline.json",
        params={
            "screen_name": "Aigis1000",
            "tweet_mode": "extended",
            "count": 20,
        },
        timeout=30,
        auth=auth,
        proxies=config.get('proxies')
    )

    posts = resp.json()
    posts.reverse()
    for post in posts:
        id_ = post['id_str']
        text = post['full_text']
        tweet = Twitter.objects(id=id_).first()
        if tweet:
            continue

        tweet = Twitter(id=id_)
        tweet.date = datetime.strptime(post['created_at'], "%a %b %d %H:%M:%S %z %Y")
        for ent in post['entities'].get('urls', []):
            text = text.replace(ent['url'], ent['expanded_url'])
        for ent in post.get('extended_entities', post['entities']).get('media', []):
            text = text.replace(ent['url'], ent['expanded_url'])
            url = ent['media_url']
            tweet.media.append(url)
        tweet.text = text
        tweet.save()
        print(str(tweet))
        for g in config.get('notify_groups', []):
            bot.send(SendGroupMessage(group=g, text=text))


if __name__ == '__main__':
    connect('aigis')
    poll_twitter([])

