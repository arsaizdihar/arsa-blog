from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField
import email_validator


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LET ME IN!")


class CommentForm(FlaskForm):
    comment_text = TextAreaField("Comment", validators=[DataRequired()], render_kw={'class': "form-control", "rows":5})
    submit = SubmitField("SUBMIT COMMENT")


class ContactForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()], render_kw={'class': "form-control", "placeholder": "Name"})
    email = StringField("Email Address", validators=[DataRequired(), Email()], render_kw={'class': "form-control", "placeholder": "Email Address"})
    phone_number = StringField("Phone Number", render_kw={'class': "form-control", "placeholder": "Phone Number"})
    message = TextAreaField("Message", validators=[DataRequired()], render_kw={'class': "form-control", "placeholder": "Message", "rows":5})
    submit = SubmitField("SEND")
