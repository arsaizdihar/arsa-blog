import tweepy
import os
ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
API_KEY = os.environ.get("TWITTER_API_KEY")
API_KEY_SECRET = os.environ.get("TWITTER_API_SECRET")

auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)


def tweet(msg, file=None):
    media = None
    try:
        if file:
            media = api.media_upload(filename="line_img", file=file)
        if media:
            post = api.update_status(msg, media_ids=[media.media_id])
        else:
            post = api.update_status(msg)
        return f"https://twitter.com/{post.user.screen_name}/status/{post.id}"
    except tweepy.error.TweepError:
        return False

