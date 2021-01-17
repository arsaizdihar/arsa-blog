from flask import Flask, render_template, redirect, url_for, flash, abort, request, make_response, session
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from forms import RegisterForm, LoginForm, CommentForm, ContactForm
from flask_gravatar import Gravatar
from urllib.parse import urlparse
from tables import db, User, BlogPost, Comment, Contact, Visitor
from admin import admin_app, check_admin, get_jkt_timezone
import os
import math

app = Flask(__name__)
app.register_blueprint(admin_app, url_prefix="/admin")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "8BYkEfBA6O6donzWlSihBXox7C0sKR6b")
ckeditor = CKEditor(app)
Bootstrap(app)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=2)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
db.app = app
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
# CONFIGURE TABLES

db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    img_url = os.environ.get("HOME_IMG_URL", "https://images.unsplash.com/photo-1519681393784-d120267933ba?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80")
    heading = os.environ.get("HOME_HEADING", "Personal Blog of Arsa")
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
    return render_template("index.html",
                           all_posts=posts,
                           page_number=page_number,
                           prev_page=prev_page,
                           next_page=next_page,
                           logged_in=current_user.is_authenticated,
                           img_url=img_url,
                           heading=heading,
                           subheading=subheading)


@app.route("/sitemap.xml")
def sitemap():
    host_components = urlparse(request.host_url)
    host_base = host_components.scheme + "://" + host_components.netloc

    # Static routes with static content
    static_urls = list()
    for rule in app.url_map.iter_rules():
        if not str(rule).startswith("/admin") and not str(rule).startswith("/user"):
            if "GET" in rule.methods and len(rule.arguments) == 0:
                url = {
                    "loc": f"{host_base}{str(rule)}"
                }
                static_urls.append(url)

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

    xml_sitemap = render_template("sitemap.xml", dynamic_urls=dynamic_urls, static_urls=static_urls,
                                  host_base=host_base)
    response = make_response(xml_sitemap)
    response.headers["Content-Type"] = "application/xml"

    return response


@app.route('/register', methods=["POST", "GET"])
def register():
    logout_user()
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
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated, title="Register Arsa Izdihar Islam's Blog")


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
            session.permanent = True
            return redirect(url_for("get_all_posts"))
        flash("Password incorrect, please try again.")
        return redirect(url_for("login"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated, title="Login Arsa Izdihar Islam's Blog")


@app.route('/user/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    if post_id == 1:
        return abort(404)
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if not check_admin():
        if not requested_post.views:
            requested_post.views = 0
        requested_post.views += 1
        db.session.commit()
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
    return render_template("post.html", post=requested_post, form=form, logged_in=current_user.is_authenticated, title=f"{requested_post.title} Arsa Izdihar Islam's Blog")


@app.route("/about")
def about():
    post = BlogPost.query.get(1)
    return render_template("about.html", logged_in=current_user.is_authenticated, post=post)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if current_user.is_authenticated:
        form.username.data = current_user.name
        form.email.data = current_user.email
    if form.validate_on_submit():
        name = form.username.data
        email = form.email.data
        phone_number = form.phone_number.data
        message = form.message.data
        new_contact = Contact(name=name, email=email, phone_number=phone_number, message=message)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for("contact"))
    return render_template("contact.html", logged_in=current_user.is_authenticated, form=form, title="Contact Arsa Izdihar Islam's Blog")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)
