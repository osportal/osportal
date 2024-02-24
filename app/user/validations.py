from wtforms.validators import ValidationError
from app.user.models import User

def check_authoriser(form, field):
    if field.object_data == field.data:
        return
    user = User.query.filter(User.username==form.username.data.lower()).first()
    if field.data == user:
        raise ValidationError('Cannot assign this user as their own leave authoriser')

def check_username_exists(form, field):
    # checks new and current data, returns if they are the same
    if field.object_data == field.data:
        return
    user = User.query.filter(User.username==field.data.lower()).first()
    if user:
        raise ValidationError('Username already exists')

def check_email_exists(form, field):
    # checks new and current data, returns if they are the same
    if field.object_data == field.data:
        return
    user = User.query.filter(User.email==field.data.lower()).first()
    if user:
        raise ValidationError('Email already exists')
