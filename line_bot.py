from flask import Blueprint, request, abort, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, \
    ButtonsTemplate, URIAction
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from html import unescape
import requests
import os
import random

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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()
    user = TweetAccount.query.filter_by(account_id=event.source.user_id).first()
    print(event.message)
    if user.id == 1 and event.message.type == "image":
        try:
            pic = line_bot_api.get_message_content(event.message.id).content
            filename = generate_filename(Image, secure_filename(pic.filename))
            mimetype = pic.mimetype
            img = Image(filename=filename, img=pic.read(), mimetype=mimetype)
            db.session.add(img)
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"{url_for('get_img', filename=img.filename)}")
            )
        except Exception as e:
            print(e)
    elif user_message == "snmptn":
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
    # elif user_message.startswith("/meme ") and len(user_message) > 6:
    #     response = requests.get('https://meme-api.herokuapp.com/gimme/' + user_message[6:])
    #     try:
    #         url = response.json()['url']
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             ImageSendMessage(original_content_url=url, preview_image_url=url)
    #         )
    #     except KeyError:
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             TextSendMessage("gaada tolol")
    #         )
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
    elif user_message.startswith("/tweet28fess ") and len(user_message) > len("/tweet28fess "):
        command_valid = True
        from_cmd, to_cmd, text_cmd = " from: ", " to: ", " text: "
        real_user_message = event.message.text
        if from_cmd in user_message and to_cmd in user_message and text_cmd in user_message:
            from_index = user_message.index(from_cmd)
            to_index = user_message.index(to_cmd)
            text_index = user_message.index(text_cmd)
            from_text = real_user_message[from_index+len(from_cmd):to_index]
            to_text = real_user_message[to_index+len(to_cmd):text_index]
            message_text = real_user_message[text_index+len(text_cmd):]
        else:
            from_text, to_text, message_text = None, None, None
            command_valid = False
        if command_valid:
            tweet_msg = f"from: {from_text}\n"\
                        f"to: {to_text}\n"\
                        f"{message_text}"
            able_tweet = True
            tweet_valid = len(tweet_msg) <= 280
            if tweet_valid:
                now = datetime.utcnow()
                account_last_tweet = now
                account = TweetAccount.query.filter_by(account_id=event.source.user_id).first()
                if not account:
                    account = TweetAccount(account_id=event.source.user_id)
                    db.session.add(account)
                if account.last_tweet:
                    account_last_tweet = datetime.strptime(account.last_tweet, "%Y-%m-%d %H:%M:%S.%f")
                    if (now - account_last_tweet).days < 1 and not account.id == 1:
                        # able_tweet = False
                        pass
                    else:
                        account.last_tweet = now.strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    account.last_tweet = now.strftime("%Y-%m-%d %H:%M:%S.%f")
                db.session.commit()
                if able_tweet:
                    url = tweet(tweet_msg)
                    if url:
                        message = f"Tweet Posted.\nurl: {url}"
                    else:
                        message = f"Tweet failed. Please try again."
                else:
                    message = f"You can't tweet until " \
                              f"{(account_last_tweet + timedelta(days=1, hours=7)).strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                message = "Text too long."
        else:
            message = "Wrong format. Should be:\n" \
                      "/tweet28fess from: to: text: "
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )
    elif user_message == "/command":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Keywords: \n"
                                 f"SNMPTN\n"
                                 f"SBMPTN\n"
                                 f"/eligiblemipa\n"
                                 f"/eligibleips\n"
                                 f"/tweet28fess from: to: text: ")
        )
