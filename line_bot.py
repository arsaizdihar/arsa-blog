from flask import Blueprint, request, abort, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, \
    ButtonsTemplate, URIAction, ImageMessage
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from html import unescape
import requests
import os
import random
import io
from werkzeug.utils import secure_filename

from admin import generate_filename
from tables import db, TweetAccount, Image
from twitter_bot import tweet
line_app = Blueprint('line_aoo', __name__, "static", "templates")
ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
KEYWORDS = ['/alipaddam', '/eligible', '/eligibleipa', '/eligibleips', '/eligiblemipa']
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def get_delta_time(year, month, day=0, hour=0):
    now = datetime.utcnow()
    now = now + timedelta(hours=7)
    snm = datetime(year=year, month=month, day=day, hour=hour)
    delta = snm - now
    day = delta.days
    clock = str(delta).split(", ")[-1]
    hour, minute, second = clock.split(':')
    second = second.split('.')[0]
    return day, hour, minute, second


def check_timeout(then, sec):
    then_datetime = datetime.strptime(then, TIME_FORMAT)
    now = datetime.utcnow()
    return (now-then_datetime).total_seconds() <= sec


def get_youtube_url(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    req = youtube.search().list(q=query, part='snippet', maxResults=1, type='video')
    res = req.execute()
    return ('https://youtu.be/' + res['items'][0]['id']['videoId']), unescape(res['items'][0]['snippet']['title'])


def get_emoji_str(hex_code):
    return f"{chr(int(f'{hex_code}', 16))}"


@line_app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    account = TweetAccount.query.filter_by(account_id=event.source.user_id).first()
    if account:
        if account.img_soon:
            if check_timeout(account.last_tweet_req, 300):
                try:
                    pic = line_bot_api.get_message_content(event.message.id)
                    file = io.BytesIO(pic.content)
                    url = tweet(account.next_tweet_msg, file)
                    file.close()
                    if url:
                        message = f"Tweet Posted.\nurl: {url}"
                    else:
                        message = f"Tweet failed. Please try again."
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=message)
                    )
                except Exception as e:
                    print(e)
            account.tweet_phase = ""
            account.last_tweet = datetime.utcnow().strftime(TIME_FORMAT)
            account.last_tweet_req = ""
            account.img_soon = False
            account.next_tweet_msg = ""
            db.session.commit()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()
    account = TweetAccount.query.filter_by(account_id=event.source.user_id).first()
    if user_message == "snmptn":
        day, hour, minute, second = get_delta_time(2021, 3, 22, 15)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text=f"Pengumuman SNMPTN\n"
                         f"🕒{day} hari {hour} jam {minute} menit {second} detik lagi 😲",
                template=ButtonsTemplate(
                    thumbnail_image_url='https://statik.tempo.co/data/2019/12/01/id_893849/893849_720.jpg',
                    title='Pengumuman SNMPTN',
                    text=f"{day} hari {hour} jam {minute} menit {second} detik lagi.",
                    actions=[
                        URIAction(
                            label='Live Countdown',
                            uri='https://snmptn.arsaizdihar.com/'
                        )
                    ]
                )
            ))
    elif user_message == "sbmptn":
        day, hour, minute, second = get_delta_time(2021, 4, 12)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"SBMPTN\n"
                                 f"{get_emoji_str('0x100071')}{day} hari {hour} jam {minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
    elif user_message.startswith('/youtube ') and len(user_message) > 9:
        query = user_message[9:]
        title, url = get_youtube_url(query)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{title}\n{url}")
        )

    elif user_message == "/meme":
        response = requests.get('https://meme-api.herokuapp.com/gimme')
        url = response.json()['url']
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=url, preview_image_url=url)
        )
    elif user_message.startswith("/number"):
        if user_message == "/number":
            message = "Keywords: \n"\
                      "- /number (number)\n"\
                      "- /number/random"
        else:
            res_type = random.choice(('math', 'trivia'))
            req = user_message[7:]
            if req == "/random":
                response = requests.get('http://numbersapi.com/random/' + res_type)
                message = response.text
            else:
                try:
                    req = int(req)
                except ValueError:
                    message = "Invalid request"
                else:
                    response = requests.get('http://numbersapi.com/' + str(req) + "/" + res_type)
                    message = response.text
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )
    elif user_message == "/cat":
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        data = response.json()
        url = data[0]['url']
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(url, url)
        )
    elif user_message == "/tweet28fess" or user_message == "/tweet28fessimg":
        if not account:
            account = TweetAccount(account_id=event.source.user_id)
            db.session.add(account)
        if user_message == "/tweet28fessimg":
            account.img_soon = True
        account.tweet_phase = "from"
        account.next_tweet_msg = "from: "
        account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("from: \n/canceltweet to cancel")
        )
    elif user_message == "/command":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Keywords: \n"
                                 "SNMPTN\n"
                                 "SBMPTN\n"
                                 "/tweet28fess\n"
                                 "/tweet28fessimg")
        )
    else:
        if account:
            phase = account.tweet_phase
            if phase:
                if user_message == "/canceltweet":
                    account.tweet_phase = ""
                    account.next_tweet_msg = ""
                    account.last_tweet_req = ""
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage("Tweet Cancelled")
                    )
                else:
                    if check_timeout(account.last_tweet_req, 300):
                        now = datetime.utcnow().strftime(TIME_FORMAT)
                        account.last_tweet_req = now
                        if phase == "from":
                            account.tweet_phase = "to"
                            account.next_tweet_msg += event.message.text + "\nto: "
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage("to: \n/canceltweet to cancel")
                            )
                        if phase == "to":
                            account.tweet_phase = "text"
                            account.next_tweet_msg += event.message.text + "\n"
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage("message: \n/canceltweet to cancel")
                            )
                        if phase == "text":
                            msg = account.next_tweet_msg + event.message.text
                            if len(account.next_tweet_msg + event.message.text) <= 280:
                                if account.img_soon:
                                    account.next_tweet_msg = msg
                                    account.tweet_phase = "img"
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage("Kirim foto yang ingin di post dalam 5 menit.")
                                    )
                                else:
                                    account.tweet_phase = ""
                                    account.next_tweet_msg = ""
                                    account.last_tweet = now
                                    account.last_tweet_req = ""
                                    url = tweet(msg)
                                    if url:
                                        message = f"Tweet Posted.\nurl: {url}"
                                    else:
                                        message = f"Tweet failed. Please try again."
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(message)
                                    )
                            else:
                                pass
                db.session.commit()
