from app.models import Country
from app.user.models import User
from app.user.validations import check_username_exists, check_email_exists
from app.utils.util_wtforms import ModelForm, choices_from_dict
from flask_admin.form.widgets import Select2Widget
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
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
    country = QuerySelectField('Country',
                               query_factory=lambda: Country.query.order_by(Country.name).all(),
                               widget=Select2Widget(),
                               allow_blank=False,
                               validators=[DataRequired()],
                               default=lambda: Country.query.filter(Country.name=='United Kingdom').first()
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
    image_file = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
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
