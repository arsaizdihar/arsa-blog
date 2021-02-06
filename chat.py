from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from tables import db, User
from flask_socketio import SocketIO

chat_app = Blueprint("chat_app", __name__, "static", "templates")
socketio = SocketIO()


@chat_app.route("/")
def chat_home():
    if current_user.is_authenticated:
        user = current_user
        all_users = [u for u in User.query.order_by("name").all() if not u == user]
        print(all_users)
    else:
        user = None
    return render_template("session.html", user=user)


def message_received(methods=('GET', 'POST')):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=('GET', 'POST')):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=message_received)


