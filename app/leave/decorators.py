from flask import redirect, flash, g, abort, url_for
from flask_login import current_user
from functools import wraps


def check_authoriser_access():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authoriser():
                flash('You are not an authoriser', 'danger')
                return redirect(url_for('leave.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def leave_enabled():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.leave.active != True:
                abort(404)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
