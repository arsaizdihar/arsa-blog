from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from forms import AddFriendForm, NewGroupForm, AddMemberForm
from tables import db, User, Chat, ChatRoom
from admin import get_jkt_timezone, get_admin_acc
from datetime import datetime
from flask_socketio import SocketIO, join_room, leave_room, send, emit

chat_app = Blueprint("chat_app", __name__, "static", "templates")
socketio = SocketIO()


def get_room_name(room):
    if room.is_group:
        return room.name
    for member in room.members:
        if not member == current_user:
            return member.name

def get_timestamp():
    # Set timestamp
    today = get_jkt_timezone(datetime.now())
    return today.strftime('%b-%d %I:%M%p')

@chat_app.context_processor
def chat_utility():
    return dict(get_room_name=get_room_name)


@chat_app.route("/")
def chat_home():
    if not current_user.is_authenticated:
        flash("Please Log In first.")
        return redirect(url_for("login"))
    rooms = current_user.chat_rooms
    if not list(rooms):
        return redirect(url_for('chat_app.add_friend'))
    first_room = rooms[0]
    return render_template("/chat/chat.html", username=current_user.name, rooms=rooms, first_room=first_room)


@chat_app.route("/new-group", methods=["POST", "GET"])
def new_group():
    form = NewGroupForm()
    form.group_member.choices = [(user.id, user.name) for user in current_user.friends]

    if form.validate_on_submit():
        group = ChatRoom(name=form.group_name.data, is_group=True)
        group.members.extend((current_user, User.query.get(form.group_member.data)))
        message = [member.name for member in group.members]
        chat = Chat(message=f"{', '.join(message)}", time="", user=User.query.get(2), room=group)
        db.session.add(chat)
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('chat_app.chat_home'))

    return render_template("chat/new-group.html", form=form)


@chat_app.route("/add-member", methods=["POST", "GET"])
def add_group_member():
    form = AddMemberForm()
    form.group_name.choices = [(room.id, room.name) for room in current_user.chat_rooms if room.is_group]
    form.group_member.choices = [(user.id, user.name) for user in current_user.friends]

    if form.validate_on_submit():
        group = ChatRoom.query.get(form.group_name.data)
        new_member = User.query.get(form.group_member.data)
        chat = group.chats[0]
        chat.message += f", {new_member.name}"
        if new_member in group.members:
            return "Error"
        new_member_chat = Chat(message=f"{new_member.name} has joined the group.",
                               time=get_timestamp(), user=get_admin_acc(), room=group)

        socketio.send({"msg": f"{new_member.name} has joined the group."}, room=group.id)
        group.members.append(new_member)
        db.session.add(new_member_chat)
        db.session.commit()
        return redirect(url_for("chat_app.chat_home"))

    return render_template("chat/add-group-member.html", form=form)


@chat_app.route("/friends")
def show_friends():
    friends = current_user.friends
    result = f"<ol>"
    for friend in friends:
        result += f"<li>{friend.name}</li>"
    result += "</ol>"
    return result


@chat_app.route("/add-friend", methods=["POST", "GET"])
def add_friend():
    form = AddFriendForm()
    form.friend_id.choices = [(user.id, user.name) for user in User.query.all()
                              if not user == current_user and user not in current_user.friends
                              and not user == get_admin_acc()]
    if form.validate_on_submit():
        friend_id = form.friend_id.data
        to_be_friend = User.query.get(friend_id)
        current_user.friends.append(to_be_friend)
        to_be_friend.friends.append(current_user)
        new_chat_room = ChatRoom()
        new_chat_room.members.extend((current_user, to_be_friend))
        db.session.add(new_chat_room)
        db.session.commit()
        return redirect(url_for('chat_app.chat_home'))

    return render_template('chat/add-friend.html', form=form)


@chat_app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""

    msg = data["msg"]
    username = data["username"]
    room_id = data["room_id"]
    chat_room = ChatRoom.query.get(room_id)
    chat = Chat(message=msg, time=get_timestamp(), user=current_user, room=chat_room)
    db.session.add(chat)
    db.session.commit()
    send({"username": username, "msg": msg, "time_stamp": get_timestamp()}, room=room_id)


@socketio.on('join')
def on_join(data):
    """User joins a room"""

    username = data["username"]
    room_id = data["room_id"]
    join_room(room_id)
    room = ChatRoom.query.get(room_id)
    chats = room.chats
    chat_list = []
    for chat in chats:
        chat_dict = {'msg': chat.message, 'time': chat.time, 'is_user': chat.user == current_user,
                     'username': chat.user.name}
        chat_list.append(chat_dict)
    if room.is_group:
        chat_list.append({'msg': chats[0].message, 'time': chats[0].time, 'is_user': False,
                          'username': 'Server'})
    # Broadcast that new user has joined
    emit('show_history', {'chats': chat_list})


@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room_id = data['room_id']
    leave_room(room_id)
    send({"msg": username + " has left the room"}, room=room_id)


