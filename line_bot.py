from flask import Blueprint, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, \
    ButtonsTemplate, URIAction, ImageMessage, QuickReply, QuickReplyButton, MessageAction
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from html import unescape
import requests
import os
import random
import io
from tables import db, TweetAccount, LineGroup
from twitter_bot import tweet
from google_search import search_google
line_app = Blueprint('line_aoo', __name__, "static", "templates")
ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
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
        if account.img_soon and account.tweet_phase == "img":
            if check_timeout(account.last_tweet_req, 300):
                account.tweet_phase = "confirm " + event.message.id
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(f"Confirmation:\n{account.next_tweet_msg}\n/send to tweet\n"
                                    f"/canceltweet to cancel",
                                    quick_reply=QuickReply(items=[
                                        QuickReplyButton(action=MessageAction("SEND", "/send")),
                                        QuickReplyButton(
                                            action=MessageAction("CANCEL", "/canceltweet"))
                                    ]))
                )
            account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
            db.session.commit()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()
    account = TweetAccount.query.filter_by(account_id=event.source.user_id).first()
    if not account:
        account = TweetAccount(account_id=event.source.user_id)
        account.name = line_bot_api.get_profile(account.account_id).display_name
        db.session.add(account)
        db.session.commit()
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
        else:
            account.img_soon = False
        account.tweet_phase = "from"
        account.next_tweet_msg = "from: "
        account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("from: \n/canceltweet to cancel",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                            ]))
        )
    elif user_message == "/command":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Keywords: \n"
                                 "SNMPTN\n"
                                 "SBMPTN\n"
                                 "/tweet28fess\n"
                                 "/tweet28fessimg\n\n"
                                 "For Fun Keywords:\n"
                                 "/meme\n"
                                 "/youtube (search query)\n"
                                 "/cat")
        )
    elif user_message == "/tumbal" and event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if not group:
            group = LineGroup(id=event.source.group_id)
            db.session.add(group)
        if group.phase == "tumbal":
            user_name = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id).display_name
            if user_name not in group.data.split("\n"):
                group.data += "\n" + user_name
                group.member_ids += "\n" + event.source.user_id
        else:
            group.phase = "tumbal"
            group.data = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id).display_name
            group.member_ids = event.source.user_id
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Daftar Tumbal" + "\n" + group.data)
        )
        db.session.commit()
    elif user_message == "/tumbalkelar" and event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if group:
            if group.phase == "tumbal" and group.data:
                member_ids = group.member_ids.split("\n")
                member = line_bot_api.get_group_member_profile(event.source.group_id, random.choice(member_ids))
                if member.picture_url:
                    messages = [
                        TextSendMessage("Yang jadi tumbal: " + member.display_name),
                        ImageSendMessage(member.picture_url, member.picture_url)
                    ]
                else:
                    messages = TextSendMessage("Yang jadi tumbal: " + member.display_name),
                line_bot_api.reply_message(
                    event.reply_token,
                    messages=messages
                )
                group.data = ""
                group.phase = ""
                group.member_ids = ""
                db.session.commit()
    elif user_message.startswith("/google ") and len(user_message) > len("/google "):
        query = event.message.text[8:]
        results = search_google(query)
        message = ""
        for result in results:
            message += f"{result['title']}\n{result['description']}\n{result['link']}\n\n"
        message = message[:-2]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )
    else:
        if account:
            phase = account.tweet_phase
            if phase:
                if user_message == "/canceltweet":
                    account.tweet_phase = ""
                    account.next_tweet_msg = ""
                    account.last_tweet_req = ""
                    account.img_soon = False
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
                                TextSendMessage("to: \n/canceltweet to cancel",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "to":
                            account.tweet_phase = "text"
                            account.next_tweet_msg += event.message.text + "\n"
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage("message: \n/canceltweet to cancel",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "text":
                            msg = account.next_tweet_msg + event.message.text
                            if len(account.next_tweet_msg + event.message.text) <= 280:
                                if account.img_soon:
                                    account.next_tweet_msg = msg
                                    account.tweet_phase = "img"
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage("Kirim foto yang ingin di post dalam 5 menit.\n"
                                                        "/canceltweet to cancel",
                                                        quick_reply=QuickReply(items=[
                                                            QuickReplyButton(
                                                                action=MessageAction("CANCEL", "/canceltweet"))
                                                        ]))
                                    )
                                else:
                                    account.tweet_phase = "confirm"
                                    account.next_tweet_msg = msg
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        TextSendMessage(f"Confirmation:\n{account.next_tweet_msg}\n/send to tweet\n"
                                                        f"/canceltweet to cancel",
                                                        quick_reply=QuickReply(items=[
                                                            QuickReplyButton(action=MessageAction("SEND", "/send")),
                                                            QuickReplyButton(
                                                                action=MessageAction("CANCEL", "/canceltweet"))
                                                        ]))
                                    )
                        if phase.startswith("confirm") and user_message == "/send":
                            account.tweet_phase = ""
                            account.last_tweet = now
                            account.last_tweet_req = ""
                            if account.img_soon:
                                msg_media_id = phase.split(" ")[-1]
                                pic = line_bot_api.get_message_content(msg_media_id)
                                file = io.BytesIO(pic.content)
                                url = tweet(account.next_tweet_msg, file)
                                file.close()
                                account.img_soon = False
                            else:
                                url = tweet(account.next_tweet_msg)
                            account.next_tweet_msg = ""
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
