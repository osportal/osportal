from flask import redirect, flash, g, abort
from flask_login import current_user
from functools import wraps

def admin_read_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.role or not current_user.role.check_admin_dash_access():
                flash('You do not have permission', 'danger')
                return redirect('/')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def entt_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.entt:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
