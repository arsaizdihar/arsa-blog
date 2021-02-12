from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin

db = SQLAlchemy()

user_friends = db.Table('friends',
                        db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
                        db.Column("friend_id", db.Integer, db.ForeignKey("users.id")))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    files = relationship("File", back_populates="file_owner")
    chats = relationship("Chat", back_populates="user")
    chat_rooms = relationship("RoomRead", back_populates="member", order_by="RoomRead.last_modified.desc()")

    friends = db.relationship('User',
                              secondary=user_friends,
                              primaryjoin=(user_friends.c.user_id == id),
                              secondaryjoin=(user_friends.c.friend_id == id))

    def __str__(self):
        return self.name


class RoomRead(db.Model):
    __tablename__ = "room_read"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), primary_key=True)
    is_read = db.Column(db.Boolean, default=False)
    last_read = db.Column(db.String(25))
    last_modified = db.Column(db.String(50))

    member = relationship("User", back_populates="chat_rooms")
    chat_room = relationship("ChatRoom", back_populates="members")


class Chat(db.Model):
    __tablename__ = "chats"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    time = db.Column(db.String(25))
    is_image = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")

    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"))
    room = relationship("ChatRoom", back_populates="chats")


class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"
    id = db.Column(db.Integer, primary_key=True)
    chats = relationship("Chat", back_populates="room", order_by='Chat.id', lazy="dynamic")
    name = db.Column(db.String(25))
    last_modified = db.Column(db.String(50))
    is_group = db.Column(db.Boolean, default=False)
    members = relationship("RoomRead", back_populates="chat_room")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="parent_post")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    views = db.Column(db.Integer)
    hidden = db.Column(db.Boolean, default=False)

    def __str__(self):
        return self.title


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)

    def __str__(self):
        return self.text


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    message = db.Column(db.Text)
    time = db.Column(db.String(50))

    def __str__(self):
        return self.email


class Visitor(db.Model):
    __tablename__ = "visitors"
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.String(100))
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))

    def __str__(self):
        return self.date_time


class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    img = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)

    def __str__(self):
        return self.filename


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    file_owner = relationship("User", back_populates="files")

    def __str__(self):
        return self.filename
