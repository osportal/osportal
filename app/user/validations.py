from wtforms.validators import ValidationError
from app.user.models import User, Role, Permission
from sqlalchemy import func

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
    if field.object_data == field.data:
        return
    user = User.query.filter(User.email==field.data.lower()).first()
    if user:
        raise ValidationError('Email already exists')

def check_role_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    role = Role.query.filter(func.lower(Role.name)==field.data.lower()).first()
    if role:
        raise ValidationError('Role already exists')

def check_permission_exists(form, field):
    if field.object_data:
        if field.object_data.lower() == field.data.lower():
            return
    perm = Permission.query.filter(func.lower(Permission.name)==field.data.lower()).first()
    if perm:
        raise ValidationError('Permission already exists')
