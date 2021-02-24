from flask import Blueprint, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta
import os

line_app = Blueprint('line_aoo', __name__, "static", "templates")
ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


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
    user_message = event.message.text
    if event.message.text.lower() == "snmptn":
        day, hour, minute, second = get_delta_time(2021, 3, 22, 15)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Pengumuman SNMPTN {day} hari {hour} jam {minute} menit {second} detik lagi"))
    elif user_message.lower() == "sbmptn":
        day, hour, minute, second = get_delta_time(2021, 4, 12)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"SBMPTN {day} hari {hour} jam {minute} menit {second} detik lagi"))
    else:
        if not event.type == 'group':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"Keywords: \n"
                                     f"snmptn\n"
                                     f"sbmptn")
            )
