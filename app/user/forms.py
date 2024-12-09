from app.extensions import db
from app.models import Site, Country
from app.user.models import User
from app.user.validations import check_username_exists, check_email_exists
from app.utils.util_wtforms import ModelForm, choices_from_dict
from flask_admin.form.widgets import Select2Widget
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms.validators import (DataRequired, Regexp, ValidationError,
                                Length, EqualTo, NumberRange,
                                Optional)
from wtforms import (StringField, PasswordField, IntegerField,
                     SubmitField, BooleanField, TextAreaField,
                     SelectField, HiddenField, DateField)
# import email validator as different name due to naming conflict with admin model Email
from wtforms.validators import Email as EmailVal
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField


class UserForm(ModelForm):
    #username_message = 'Alphanumeric characters only please.'
    username = StringField('Username',
                           validators=[
                               check_username_exists,
                               DataRequired(),
                               Length(min=2, max=113),
                               #Regexp(r'^[\w]+$', message=username_message)
                               ])
    email = StringField('Email', validators=[check_email_exists, DataRequired(), EmailVal()])
    first_name = StringField('First Name', validators=[
                               Optional(),
                               Length(min=2, max=50),
                               ])
    middle_name = StringField('Middle Name', validators=[
                               Optional(),
                               Length(min=2, max=50),
                               ])
    last_name = StringField('Last Name', validators=[
                               Optional(),
                               Length(min=2, max=50),
                               ])
    dn = StringField('Display Name', validators=[
                               Optional(),
                               Length(min=2, max=50),
                               ])
    contact_number = StringField('Contact Number', validators=[
                               Optional(),
                               Length(min=1, max=25),
                               ])
    site = QuerySelectField('Site',
                               query_factory=lambda: Site.query.all(),
                               widget=Select2Widget(),
                               allow_blank=True,
                               validators=[Optional()]
                               )


class RegistrationForm(UserForm):
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         Length(min=8)])
    password2 = PasswordField('Confirm Password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                          message='Passwords must match')])



class LoginForm(FlaskForm):
    identity = StringField('Username', validators=[DataRequired(), Length(3, 113)])
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 128)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), EmailVal()])
    image_file = FileField('Update Profile Picture',
                           validators=[FileAllowed(['jpg','jpeg','png','gif','webp','tiff','bmp']),
                                       FileSize(max_size=15*1024*1024,
                                                message='File size should be less than 15MB')
                                      ]
                           )
    bio = TextAreaField('Bio', validators=[Optional(), Length(min=2,max=255)])
    submit = SubmitField('Update')


    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please use another')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please use another')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), EmailVal()])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         Length(min=8)])
    password2 = PasswordField('Confirm Password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                          message='Passwords must match')])
    submit = SubmitField('Reset Password')
