from flask import Blueprint, abort, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps
from flask_login import current_user
from werkzeug.security import generate_password_hash
from forms import CreatePostForm, LoginForm, UploadImageForm
from werkzeug.utils import secure_filename
from tables import db, User, BlogPost, Contact, Comment, Image


admin_app = Blueprint("admin_app", __name__, "static", "templates")


def get_admin_acc():
    return User.query.get(2)


def generate_filename(model, filename):
    i = 0
    name_list = filename.split(".")
    file_type = name_list[-1]
    first_name = name_list[0]
    last_name = first_name
    while model.query.filter_by(filename=f"{last_name}.{file_type}").first():
        i += 1
        last_name = first_name + str(i)
    return f"{last_name}.{file_type}"


def get_jkt_timezone(date_time: datetime):
    return date_time + timedelta(hours=7)


def check_admin():
    admin_ids = [1, 2]
    if current_user.is_authenticated:
        if current_user.id in admin_ids:
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


@admin_app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        if BlogPost.query.filter_by(title=form.title.data).first():
            form.title.errors.append("This title is already exist.")
        else:
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
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@admin_app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
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


@admin_app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    for comment in post_to_delete.comments:
        db.session.delete(comment)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@admin_app.route("/edit", methods=["GET", "POST"])
@admin_only
def edit_admin():
    form = LoginForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("edit-admin.html", form=form, logged_id=current_user.is_authenticated)


@admin_app.route("/contact")
@admin_only
def show_contacts():
    contact_id = request.args.get("id")
    if contact_id:
        contact_id = int(contact_id)
        contact_to_delete = Contact.query.get(contact_id)
        db.session.delete(contact_to_delete)
        db.session.commit()
        return redirect(url_for("admin_app.show_contacts"))
    all_contacts = Contact.query.all()
    return render_template("show-contact.html", contacts=all_contacts, logged_in=True)


@admin_app.route("/users")
@admin_only
def show_users():
    all_users = User.query.all()
    return render_template("show-users.html", users=all_users, logged_in=True)


@admin_app.route("/delete-comment/<int:post_id>")
@admin_only
def delete_comment(post_id):
    comment_id = request.args.get("comment_id")
    comment = Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for("show_post", post_id=post_id))


@admin_app.route("/upload", methods=["POST", "GET"])
@admin_only
def upload_img():
    form = UploadImageForm()
    if form.validate_on_submit():
        pic = form.file.data
        filename = generate_filename(Image, secure_filename(pic.filename))
        mimetype = pic.mimetype
        img = Image(filename=filename, img=pic.read(), mimetype=mimetype)
        db.session.add(img)
        db.session.commit()
        return redirect(f"{request.url_root}/admin/image/")
    return render_template("upload-img.html", form=form, logged_in=True)


