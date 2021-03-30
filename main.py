# -*- coding: utf-8 -*-
# flask import
from flask import Flask, render_template, redirect, url_for, flash, abort, request, make_response, session, Response, send_file
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_gravatar import Gravatar
from flask_migrate import Migrate, MigrateCommand

# utils
from datetime import datetime, timedelta
from urllib.parse import urlparse
from jinja2 import Markup
import io
import os
import math
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_script import Manager

# locals
from forms import RegisterForm, LoginForm, CommentForm, ContactForm, UploadFileForm
from tables import db, User, BlogPost, Comment, Contact, Image, File
from admin import admin_app, check_admin, get_jkt_timezone, upload_img, generate_filename
from chat import chat_app, socketio, send_email


app = Flask(__name__)


# admin app
app.register_blueprint(admin_app, url_prefix="/admins")

# chat app
app.register_blueprint(chat_app, url_prefix="/chat")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "8BYkEfBA6O6donzWlSihBXox7C0sKR6b")

# secure all endpoints
app.wsgi_app = ProxyFix(app.wsgi_app)

ckeditor = CKEditor(app)
Bootstrap(app)

socketio.init_app(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=2)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
db.app = app
db.init_app(app)
db.create_all()

# db migrations
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


# /admin page
class UserModelView(ModelView):
    def is_accessible(self):
        return check_admin()

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return abort(403)


class HomeView(AdminIndexView):
    @expose("/")
    def index(self):
        if check_admin():
            return self.render('admin.html')
        else:
            return redirect(url_for("get_all_posts"))


class ImageView(ModelView):
    def _list_thumbnail(view, context, model, name):
        return Markup(
            '<img src="%s" style="height:400px">' %
            url_for('get_img', filename=model.filename)
        )

    def _img_url(view, context, model, name):
        return Markup(
            '<a href="{}">{}</a>'.format(
            url_for('get_img', filename=model.filename), f"image {model.id}")
        )

    column_list = ('url', 'filename', 'img')

    column_formatters = {
        'img': _list_thumbnail,
        'url': _img_url
    }

    @expose('/new', methods=["POST", "GET"])
    def create_view(self):
        return upload_img()


class FileView(ModelView):
    def _file_embed(view, context, model, name):
        if model.mimetype.startswith("video"):
            return Markup(
                model.filename +
                '<br>'
                '<video width="320" height="240" controls>'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support the video tag.'
                '</video>'.format(url_for("get_file", filename=model.filename))
            )
        elif model.mimetype.startswith("image"):
            return Markup(
                '<img src="%s" style="height:400px">' %
                url_for('get_file', filename=model.filename)
            )

    def _file_url(view, context, model, name):
        return Markup(
            '<a href="{}">{}</a>'.format(
            url_for('get_file', filename=model.filename), "Download")
        )

    column_list = ('id', 'filename', 'file', 'preview')

    column_formatters = {
        'file': _file_url,
        "preview": _file_embed,
    }

    @expose('/new', methods=["POST", "GET"])
    def create_view(self):
        return upload_file()


admin = Admin(app=app, index_view=HomeView())
admin.add_views(
    UserModelView(User, db.session),
    UserModelView(BlogPost, db.session),
    UserModelView(Comment, db.session),
    UserModelView(Contact, db.session),
    ImageView(Image, db.session),
    FileView(File, db.session),
)

# add function to jinja
app.jinja_env.globals.update(check_admin=check_admin)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# home route
@app.route('/')
def get_all_posts():
    # get img_url, heading, and subheading for the page
    img_url = os.environ.get("HOME_IMG_URL", "https://images.unsplash.com/photo-1519681393784-d120267933ba?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80")
    heading = os.environ.get("HOME_HEADING", "Personal Blog of Arsa")
    subheading = os.environ.get("HOME_SUBHEADING", "test")

    # check for page_number request if there is any
    page_number = request.args.get("page_number")

    # count total page_number and cut the posts
    if not page_number:
        page_number = 1
    else:
        page_number = int(page_number)
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    if posts:
        del posts[-1]

    # just show post that isn't hidden
    if not check_admin():
        posts = [post for post in posts if not post.hidden]
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


# sitemap route
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
        if post.id != 1 and not post.hidden:
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


# register route
@app.route('/register', methods=["POST", "GET"])
def register():
    # logout the user
    logout_user()

    form = RegisterForm()
    if form.validate_on_submit():

        # check if the email already exist
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        # make a new user
        new_user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8),
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        send_email(form.email.data, "Welcome to arsaiz.com!", f"Hello {form.name.data}!\nCheck my chat app at www.arsaiz.com/chat")

        # login the user immediately
        login_user(new_user)
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=form, logged_in=current_user.is_authenticated, title="Register Arsa Izdihar Islam's Blog")


# login route
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


# logout route
@app.route('/user/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# show post route
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    # don't show the about post page
    if post_id == 1:
        return abort(404)
    form = CommentForm()
    requested_post = BlogPost.query.get_or_404(post_id)
    if not check_admin():

        # don't show the hidden post
        if requested_post.hidden:
            return abort(404)
        if not requested_post.views:
            requested_post.views = 0

        # increment the post views
        requested_post.views += 1
        db.session.commit()

    # if user leave a comment
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

        # redirect to log in page if not authenticated
        flash("You need to log in first before leaving any comments.")
        return redirect(url_for("login"))

    return render_template("post.html", post=requested_post, form=form, logged_in=current_user.is_authenticated, title=f"{requested_post.title} Arsa Izdihar Islam's Blog")


@app.route("/about")
def about():
    # the about page is the first post in the database
    post = BlogPost.query.get(1)
    return render_template("about.html", logged_in=current_user.is_authenticated, post=post)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    # if user is authenticated, fill the username and email field automatically
    if current_user.is_authenticated:
        form.username.data = current_user.name
        form.email.data = current_user.email

    if form.validate_on_submit():
        name = form.username.data
        email = form.email.data
        phone_number = form.phone_number.data
        message = form.message.data
        time = get_jkt_timezone(datetime.now())
        new_contact = Contact(name=name, email=email, phone_number=phone_number, message=message, time=time)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for("contact"))

    return render_template("contact.html", logged_in=current_user.is_authenticated, form=form, title="Contact Arsa Izdihar Islam's Blog")


@app.route("/img/<filename>")
def get_img(filename):
    """Get image from the database"""
    img = Image.query.filter_by(filename=filename).first()
    if not img:
        return abort(404)
    return Response(img.img, mimetype=img.mimetype)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    """Upload a file to the database"""

    if not current_user.is_authenticated:
        flash("You need to log in or sign up before uploading file.")
        return redirect(url_for("login"))

    form = UploadFileForm()
    if form.validate_on_submit():
        pic = form.file.data
        filename = generate_filename(File, pic.filename)
        mimetype = pic.mimetype
        file = File(filename=filename, file=pic.read(), mimetype=mimetype, file_owner=current_user)
        db.session.add(file)
        db.session.commit()
        return redirect(url_for("get_files"))
    return render_template("upload-img.html", form=form, logged_in=True, file=True)


@app.route("/file/<filename>")
def get_file(filename):
    """Get the file from the database"""
    file = File.query.filter_by(filename=filename).first()
    if not file:
        return abort(404)

    # if user ask to download, send as attachment
    if request.args.get("download"):
        return send_file(
            io.BytesIO(file.file),
            mimetype=file.mimetype,
            as_attachment=True,
            attachment_filename=file.filename,
        )

    return send_file(
        io.BytesIO(file.file),
        mimetype=file.mimetype,
        as_attachment=False,
    )


@app.route("/files")
def get_files():
    """Get the file that the user owned"""
    file_id = request.args.get("file_id")

    # delete the file from the database
    if file_id:
        file_to_delete = File.query.get(file_id)
        if file_to_delete.file_owner == current_user or check_admin():
            db.session.delete(File.query.get(file_id))
            db.session.commit()

    # show the file that someone owned even not authenticated
    owner_name = request.args.get("owner")
    if owner_name:
        owner = User.query.filter_by(name=owner_name).first()
        if owner:
            files = File.query.filter_by(file_owner=owner).order_by("id").all()
            return render_template("show_files.html", logged_in=False, files=files)

    if current_user.is_authenticated:
        files = File.query.filter_by(file_owner=current_user).order_by("id").all()
        return render_template("show_files.html", logged_in=True, files=files)

    return abort(401)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
