from app.models import get_class_by_tablename
from app.posts.models import Post
from flask import redirect, flash, g, abort, url_for
from flask_login import current_user
from functools import wraps


def setup_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.admin.models import Settings
            settings = Settings.query.first_or_404()
            if settings.setup == True:
                return redirect(url_for('main.setup'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
