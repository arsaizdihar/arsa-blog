import math

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from forms import AddFriendForm, NewGroupForm, AddMemberForm, ProfileForm, ChangePasswordForm, DeleteGroupForm
from tables import db, User, Chat, ChatRoom, Image, RoomRead
from admin import get_jkt_timezone, get_admin_acc, generate_filename, admin_only
from datetime import datetime
from flask_socketio import SocketIO, join_room, leave_room, send, emit, rooms
from PIL import Image as PilImage
import io
chat_app = Blueprint("chat_app", __name__, "static", "templates")
socketio = SocketIO()


def get_room_name(room):
    if room.is_group:
        return room.name
    for assoc in room.members:
        if not assoc.member == current_user:
            return assoc.member.name


def modified_update(room=None, commit=False):
    today = get_jkt_timezone(datetime.now()).strftime('%Y-%m-%d %H:%M:%S:%f')
    if room:
        room.last_modified = today
        for assoc in room.members:
            assoc.last_modified = today
        if commit:
            db.session.commit()
    return today


def room_get_datetime(room):
    return datetime.strptime(room.last_modified, '%Y-%m-%d %H:%M:%S:%f')


def room_get_members(room):
    return [assoc.member for assoc in room.members]


def user_get_rooms(user):
    return [assoc.chat_room for assoc in user.chat_rooms]


def get_timestamp():
    # Set timestamp
    today = get_jkt_timezone(datetime.now())
    return today.strftime('%b-%d %I:%M%p')


def make_room_read(room=None, user=None, users=None, user_id=None, room_id=None, commit=False):
    if room and user:
        a = RoomRead(last_modified=modified_update())
        a.member = user
        a.chat_room = room
        db.session.add(a)
    elif room_id and user_id:
        a = RoomRead(last_modified=modified_update())
        user = User.query.get(user_id)
        room = ChatRoom.query.get(room_id)
        a.member = user
        a.chat_room = room
        db.session.add(a)
    elif room and users:
        for user in users:
            a = RoomRead(last_modified=modified_update())
            a.member = user
            a.chat_room = room
            db.session.add(a)
    if commit:
        db.session.commit()


def delete_group(room, commit=False):
    assocs = room.members
    for assoc in assocs:
        db.session.delete(assoc)
    db.session.delete(room)
    for chat in room.chats:
        if chat.is_image:
            filename = chat.message.split("/")[-1]
            image = Image.query.filter_by(filename=filename).first()
            if image:
                db.session.delete(image)
        db.session.delete(chat)
    if commit:
        db.session.commit()


def JPEGSaveWithTargetSize(im, target):
    """Save the image as JPEG with the given name at best quality that makes less than "target" bytes"""
    Qmin, Qmax = 15, 50
    im = im.convert('RGB')
    while Qmin <= Qmax:
        m = math.floor((Qmin + Qmax) / 2)
        buffer = io.BytesIO()

        im.save(buffer, format="JPEG", quality=m)
        s = buffer.getbuffer().nbytes
        print(s)
        if s <= target:
            break
        elif s > target:
            Qmax = m - 1
    return buffer.getvalue()


@chat_app.context_processor
def chat_utility():
    return dict(get_room_name=get_room_name)


@chat_app.route("/")
def chat_home():
    if not current_user.is_authenticated:
        flash("Please Log In first.")
        return redirect(url_for("login"))
    chat_rooms = []
    for assoc in current_user.chat_rooms:
        room = assoc.chat_room
        room_name = get_room_name(room)
        chat_rooms.append({"id": room.id, "name": room_name, "is_read": assoc.is_read})
    if not list(chat_rooms):
        return redirect(url_for('chat_app.add_friend'))
    return render_template("/chat/chat.html", username=current_user.name, rooms=chat_rooms)


@chat_app.route("/new-group", methods=["POST", "GET"])
def new_group():
    form = NewGroupForm()
    form.group_member.choices = [(user.id, user.name) for user in current_user.friends]

    if form.validate_on_submit():
        group = ChatRoom(name=form.group_name.data, is_group=True, last_modified=modified_update())
        new_member = User.query.get(form.group_member.data)
        make_room_read(room=group, users=(current_user, new_member), commit=True)
        message = [assoc.member.name for assoc in group.members]
        chat = Chat(message=f"{', '.join(message)}", time="", user=User.query.get(2), room=group)
        db.session.add(chat)
        db.session.commit()
        return redirect(url_for('chat_app.chat_home'))

    return render_template("chat/new-group.html", form=form)


@chat_app.route("/add-member", methods=["POST", "GET"])
def add_group_member():
    form = AddMemberForm()
    form.group_name.choices = [(0, 'Please select an option')] + [(room.id, room.name) for room in user_get_rooms(current_user) if room.is_group]
    form.group_member.choices = [(0, 'Select Group')]

    if request.method == "POST":
        group = ChatRoom.query.get(form.group_name.data)
        modified_update(group)
        new_member = User.query.get(form.group_member.data)
        if not group:
            form.group_name.errors.append('Please select a valid option.')
        if not new_member:
            form.group_member.errors.append('Please select valid option.')
        if group and new_member:
            chat = group.chats[0]
            chat.message += f", {new_member.name}"
            if new_member in room_get_members(group):
                return "Error"
            new_member_chat = Chat(message=f"{new_member.name} has joined the group.",
                                   time=get_timestamp(), user=get_admin_acc(), room=group)
            socketio.send({"msg": f"{new_member.name} has joined the group."}, to=group.id)
            make_room_read(room=group, user=new_member)
            db.session.add(new_member_chat)
            db.session.commit()
            return redirect(url_for("chat_app.chat_home"))

    return render_template("chat/add-group-member.html", form=form)


@chat_app.route("/add-member/<int:group_id>")
@login_required
def get_new_member(group_id):
    group = ChatRoom.query.get(group_id)
    if group:
        members = room_get_members(group)
        if current_user not in members:
            return jsonify({'error': "bad request, group isn't exist."})
        new_members = [friend for friend in current_user.friends if friend not in members]
        new_members_dict = {'new_members': [{'id': user.id, 'username': user.name} for user in new_members]}
        return jsonify(new_members_dict)
    return jsonify({'error': "bad request, group isn't exist."}), 400


@chat_app.route("/group-member/<int:group_id>")
def get_group_member(group_id):
    group = ChatRoom.query.get(group_id)
    if group:
        members_dict = {'members':
                            [{"id": member.id, 'name': member.name} for member in room_get_members(group)]}
        return jsonify(members_dict)


@chat_app.route("/add-friend", methods=["POST", "GET"])
def add_friend():
    autocomplete = [user.name for user in User.query.all() if not user == current_user and user not in current_user.friends]
    if request.method == "POST":
        friend_id = request.form.get("friend_id")
        to_be_friend = User.query.get(friend_id)
        current_user.friends.append(to_be_friend)
        to_be_friend.friends.append(current_user)
        new_chat_room = ChatRoom(last_modified=modified_update())
        make_room_read(room=new_chat_room, users=(current_user, to_be_friend))
        db.session.add(new_chat_room)
        db.session.commit()
        return redirect(url_for('chat_app.chat_home'))

    return render_template('chat/add-friend.html', autocomplete=autocomplete)


@chat_app.route("/profile", methods=["POST", "GET"])
@login_required
def profile():
    form = ProfileForm(username=current_user.name, email=current_user.email)

    if form.validate_on_submit():
        current_user.name = form.username.data
        current_user.email = form.email.data
        for room in user_get_rooms(current_user):
            if room.is_group:
                room.chats[0].message = ", ".join(member.name for member in room_get_members(room))
        db.session.commit()
        flash("Save changed successfully.")
    return render_template("chat/profile.html", form=form)


@chat_app.route("/change-password", methods=["POST", "GET"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.last_password.data):
            current_user.password = generate_password_hash(form.new_password1.data,
                                                           method="pbkdf2:sha256", salt_length=8)
            flash("Password changed successfully.")
            db.session.commit()
        else:
            form.last_password.errors.append("Your password is invalid.")
    return render_template("chat/change_password.html", form=form)


@chat_app.route("/group/delete", methods=["POST", "GET"])
def delete_group():
    form = DeleteGroupForm()
    user_rooms = user_get_rooms(current_user)
    form.group.choices = [(room.id, room.name) for room in user_rooms if room.is_group]
    if form.validate_on_submit():
        group_to_delete = ChatRoom.query.get(form.group.data)
        if group_to_delete not in user_rooms:
            return redirect("chat/401.html"), 401
        db.session.commit()
        return redirect(url_for("chat_app.chat_home"))
    return render_template("chat/delete-group.html", form=form)


@chat_app.route("/user/search/<name>")
def search_user_by_name(name):
    look_for = f"%{name}%"
    users = User.query.filter(User.name.ilike(look_for)).all()
    response_list = [{"id": user.id, "name": user.name} for user in users if user not in current_user.friends and not user == current_user]
    if response_list:
        return jsonify({"users": response_list})
    return jsonify({"Error": "No user has that name"})


@chat_app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('chat/404.html'), 404


@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""
    msg = data["msg"]
    username = data["username"]
    room_id = data["room_id"]
    chat_room = ChatRoom.query.get(room_id)
    for assoc in chat_room.members:
        assoc.is_read = False
    chat = Chat(message=msg, time=get_timestamp(), user=current_user, room=chat_room)
    modified_update(chat_room)
    db.session.add(chat)
    db.session.commit()
    send({"username": username, "msg": msg, "time_stamp": get_timestamp()}, room=room_id)
    socketio.emit("notify_chat", {"room_id": room_id})


@socketio.on('read')
def read_callback(data):
    assoc = RoomRead.query.filter_by(room_id=data['room_id'], user_id=current_user.id).first()
    assoc.is_read = True
    db.session.commit()


@socketio.on('join')
def on_join(data):
    """User joins a room"""
    username = data["username"]
    room_id = data["room_id"]
    join_room(room_id)
    room = ChatRoom.query.get(room_id)
    assoc = RoomRead.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    assoc.is_read = True
    assoc.last_read = modified_update()
    db.session.commit()
    chats = room.chats
    chat_list = []
    for chat in chats:
        chat_dict = {'msg': chat.message, 'time': chat.time, 'is_user': chat.user == current_user,
                     'username': chat.user.name, "is_image": chat.is_image}
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


@socketio.on("upload-img")
def upload_image(data):
    print(data)


@chat_app.route("/broadcast/<msg>")
@admin_only
def broadcast(msg):
    for room in ChatRoom.query.all():
        broadcast_chat = Chat(message=msg,
                               time=get_timestamp(), user=get_admin_acc(), room=room)
        db.session.add(broadcast_chat)
    db.session.commit()
    socketio.send({"msg": msg})
    return redirect(url_for('chat_app.chat_home'))


@chat_app.route("/upload_ajax", methods=["POST"])
def upload_ajax():
    pic = request.files['image-upload']
    room_id = request.headers.get("room_id")
    filename = generate_filename(Image, pic.filename).split(".")[0] + ".jpeg"
    message = url_for("get_img", filename=filename)

    pil_image = PilImage.open(io.BytesIO(pic.read()))
    img = Image(filename=filename, img=JPEGSaveWithTargetSize(pil_image, 300000), mimetype="image/jpeg")

    room = ChatRoom.query.get(room_id)

    chat = Chat(message=message, time=get_timestamp(),
                is_image=True,
                user=current_user,
                room=room)
    modified_update(room)
    db.session.add(chat)
    db.session.add(img)
    db.session.commit()
    socketio.send({"username": current_user.name, "msg": message, "time_stamp": get_timestamp(), "is_image": True},
                  to=room_id)
    return "", 200


@chat_app.route("/get-unread")
def get_room_unread():
    rooms_unread = [assoc.chat_room for assoc in current_user.chat_rooms if not assoc.is_read]
    result = [{"room_id": room.id, "room_name": get_room_name(room)} for room in rooms_unread]
    return jsonify({"rooms": result})
