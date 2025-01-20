from app.admin.utils import get_settings_value
from flask import redirect, flash, abort, render_template
from flask_login import current_user
from functools import wraps


def permission_required(*obj, crud):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # if index page has permissions on it
            # below can and will be recursive therefore
            # index page has to be constant without permissions
            # perhaps index page needs to be a dashboard?
            # TODO remove dynamic index page and/or user permissions
            for o in obj:
                if current_user.permission(o, crud=crud):
                    return f(*args, **kwargs)
            flash('You do not have permission', 'danger')
            return redirect('/')
        return decorated_function
    return decorator


def anonymous_required(url='/'):
    """ If user is already signed-in redirect them to specified url """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                flash('You must logout to perform this action', 'danger')
                return redirect(url)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def forgot_password_enabled():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if get_settings_value('forgot_password') != True:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
