from flask import redirect, flash, g, abort
from flask_login import current_user
from functools import wraps

def event_enabled():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.event.active != True:
                abort(404)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
