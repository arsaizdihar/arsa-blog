from flask import Flask, render_template, redirect, url_for, flash, abort, request, make_response
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from urllib.parse import urlparse
import os
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "8BYkEfBA6O6donzWlSihBXox7C0sKR6b")
ckeditor = CKEditor(app)
Bootstrap(app)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# # MY_EMAIL = os.environ.get("EMAIL")
# # MY_PASSWORD = os.environ.get("PASSWORD")
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USERNAME'] = MY_EMAIL
# app.config['MAIL_PASSWORD'] = MY_PASSWORD
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
# mail = Mail(app=app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
# CONFIGURE TABLES


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


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


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    message = db.Column(db.Text)


class Visitor(db.Model):
    __tablename__ = "visitors"
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.String(100))
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))


db.create_all()


def get_jkt_timezone(date_time: datetime):
    return date_time + timedelta(hours=7)


def check_admin():
    if current_user.is_authenticated:
        if current_user.id == 1:
            return True
        return False
    return False


def admin_only(f):
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        if check_admin():
            return f(*args, **kwargs)
        return abort(404)
    return wrapped_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    img_url = os.environ.get("HOME_IMG_URL", "https://images.unsplash.com/photo-1519681393784-d120267933ba?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80")
    subheading = os.environ.get("HOME_SUBHEADING", "test")
    page_number = request.args.get("page_number")
    if current_user.is_authenticated:
        if current_user.id != 1:
            visitor = Visitor(date_time=get_jkt_timezone(datetime.now()), ip=request.remote_addr, user_agent=current_user.name)
            db.session.add(visitor)
            db.session.commit()
    else:
        visitor = Visitor(date_time=get_jkt_timezone(datetime.now()), ip=request.remote_addr, user_agent=request.user_agent.string)
        db.session.add(visitor)
        db.session.commit()
    if not page_number:
        page_number = 1
    else:
        page_number = int(page_number)
    posts = BlogPost.query.order_by("id").all()
    del posts[0]
    posts.reverse()
    max_page = math.ceil(len(posts) / 5)
    next_page = max_page > page_number
    prev_page = page_number > 1
    return render_template("index.html", all_posts=posts, page_number=page_number, prev_page=prev_page, next_page=next_page, logged_in=current_user.is_authenticated, img_url=img_url, subheading=subheading)


@app.route("/sitemap.xml")
def sitemap():
    host_components = urlparse(request.host_url)
    host_base = host_components.scheme + "://" + host_components.netloc

    # Static routes with static content
    # static_urls = list()
    # for rule in app.url_map.iter_rules():
    #     if not str(rule).startswith("/admin") and not str(rule).startswith("/user"):
    #         if "GET" in rule.methods and len(rule.arguments) == 0:
    #             url = {
    #                 "loc": f"{host_base}{str(rule)}"
    #             }
    #             static_urls.append(url)

    # Dynamic routes with dynamic content
    dynamic_urls = list()
    blog_posts = BlogPost.query.all()
    for post in blog_posts:
        if post.id != 1:
            url = {
                "loc": f"{host_base}/post/{post.id}",
                "lastmod": datetime.strptime(post.date, "%B %d, %Y").strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            dynamic_urls.append(url)

    xml_sitemap = render_template("sitemap.xml", dynamic_urls=dynamic_urls,
                                  host_base=host_base)
    response = make_response(xml_sitemap)
    response.headers["Content-Type"] = "application/xml"

    return response


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        new_user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8),
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("This email does not exist, please try again.")
            return redirect(url_for("login"))
        if check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("get_all_posts"))
        flash("Password incorrect, please try again.")
        return redirect(url_for("login"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    if post_id == 1:
        return abort(404)
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(
                author_id=current_user.id,
                post_id=post_id,
                text=form.comment_text.data
            )
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=post_id))
        flash("You need to log in first before leaving any comments.")
        return redirect(url_for("login"))
    return render_template("post.html", post=requested_post, form=form, logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    post = BlogPost.query.get(1)
    return render_template("about.html", logged_in=current_user.is_authenticated, post=post)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        name = data["username"]
        email = data["email"]
        phone_number = data['phone_number']
        message = data["message"]
        new_contact = Contact(name=name, email=email, phone_number=phone_number, message=message)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for("contact"))
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=get_jkt_timezone(datetime.now()).strftime("%B %d, %Y"),
            views=0
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()

        # POST FOR ABOUT
        if post.id == 1:
            return redirect(url_for("about"))
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    for comment in post_to_delete.comments:
        db.session.delete(comment)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/edit-admin", methods=["GET", "POST"])
@admin_only
def edit_admin():
    form = LoginForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("edit-admin.html", form=form, logged_id=current_user.is_authenticated)


@app.route("/delete-comment/<int:post_id>")
def delete_comment(post_id):
    comment_id = request.args.get("comment_id")
    comment = Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for("show_post", post_id=post_id))


@app.route("/contact/show")
@admin_only
def show_contacts():
    contact_id = request.args.get("id")
    if contact_id:
        contact_id = int(contact_id)
        contact_to_delete = Contact.query.get(contact_id)
        db.session.delete(contact_to_delete)
        db.session.commit()
        return redirect(url_for("show_contacts"))
    all_contacts = Contact.query.all()
    return render_template("show-contact.html", contacts=all_contacts, logged_in=True)


@app.route("/users")
@admin_only
def show_users():
    all_users = User.query.all()
    return render_template("show-users.html", users=all_users, logged_in=True)


@app.route("/visitors")
@admin_only
def show_visitors():
    visitor_id = request.args.get("id")
    is_delete_all = request.args.get("delete_all")
    if is_delete_all:
        Visitor.query.delete()
        db.session.commit()
    elif visitor_id:
        visitor_id = int(visitor_id)
        visitor_to_delete = Visitor.query.get(visitor_id)
        db.session.delete(visitor_to_delete)
        db.session.commit()
        return redirect(url_for("show_visitors"))
    all_visitors = Visitor.query.all()
    all_visitors.reverse()
    return render_template("show-visitors.html", visitors=all_visitors, logged_in=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)
