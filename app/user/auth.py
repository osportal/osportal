from app.user.models import User
from werkzeug.security import check_password_hash


def auth_user_db(username, password):
    # if username not provided or blank, gtfo
    if username is None or username == "":
        return None

    user = User.find_by_identity(username)

    # if user does not exist, gtfo
    if not user:
        return None

    # If user exists but account is disabled, gtfo
    if not user.active:
        return None

    # If user exists, is active and password matches - return user.
    # If not, gtfo
    if check_password_hash(user.password, password):
        return user
    else:
        return None
