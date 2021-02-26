from flask import Blueprint, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from html import unescape
import requests
import os

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
    if user_message == "snmptn":
        day, hour, minute, second = get_delta_time(2021, 3, 22, 15)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Pengumuman SNMPTN\n"
                                 f"{get_emoji_str('0x100071')}{day} hari {hour} jam {minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
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
    elif user_message.startswith("/meme ") and len(user_message) > 6:
        response = requests.get('https://meme-api.herokuapp.com/gimme/' + user_message[6:])
        url = response.json()['url']
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=url, preview_image_url=url)
        )
    elif user_message == "/command":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Keywords: \n"
                                 f"SNMPTN\n"
                                 f"SBMPTN\n"
                                 f"/eligiblemipa\n"
                                 f"/eligibleips")
        )
