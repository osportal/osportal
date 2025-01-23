from flask import (render_template, request, url_for, redirect, flash, abort,
                   Blueprint, g, current_app)
from flask_login import login_user, current_user, logout_user, login_required
from app.extensions import db
from app.models import Country
from app.user.forms import RegistrationForm
from app.user.models import User, Role
from app.admin.models import Settings, Page
from app.admin.utils import get_settings_value
from app.posts.models import Post, Comment

main = Blueprint('main', __name__)


@main.route('/setup', methods=['GET', 'POST'])
def setup():
    user = User()
    settings = Settings.query.first()
    if settings.setup == False:
        return redirect("/")
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(user)
            user.password = User.encrypt_password(form.password.data)
            su_role = Role.query.first_or_404() # should get us superuser
            user.role = su_role
            user.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            settings.setup=False
            settings.save()
            flash(f'User successfully registered', 'success')
            return redirect(url_for('user.login'))
    return render_template('setup.html', form=form)


@main.route('/home')
@login_required
def index():
    return redirect(url_for('posts.index'))
