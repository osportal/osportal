from flask import render_template, request, url_for, redirect, flash, abort, Blueprint, g, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app.extensions import db
from app.models import Country, get_class_by_tablename
from app.user.forms import RegistrationForm
from app.user.models import User, Role
from app.admin.models import Settings, Page
from app.admin.utils import get_settings_value
from app.posts.models import Post, Comment
from sqlalchemy_continuum import transaction_class
from sqlalchemy_continuum.utils import versioned_objects, count_versions

main = Blueprint('main', __name__)

allowed_models = ['user','role', 'leave', 'entt']

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
            countries=Country()
            settings.setup=False
            settings.save()
            flash(f'User successfully registered', 'success')
            return redirect(url_for('user.login'))
    return render_template('setup.html', form=form)

@main.route('/home')
@login_required
def index():
    return redirect(url_for('posts.index'))


@main.route('/<model_name>/<int:instance_id>/changes', methods=['GET', 'POST'], defaults={'page':1})
@main.route('/<model_name>/<int:instance_id>/changes/page/<int:page>', methods=['GET', 'POST'])
def changes(model_name, instance_id, page):
    if model_name not in allowed_models:
        abort(404)
    # initial model query
    model = get_class_by_tablename(model_name)
    instance = model.query.get_or_404(instance_id)
    # version model
    v_model_name = model_name + "_version"
    v_model = get_class_by_tablename(v_model_name)
    # transaction model
    t_model = get_class_by_tablename('transaction')
    versions = v_model.query.filter_by(id=instance_id).join(t_model,
                                                            t_model.id==v_model.transaction_id).order_by(t_model.issued_at.desc()).paginate(page=page, per_page=30)
    # version count
    count = count_versions(instance)
    return render_template('changes.html', instance=instance, versions=versions, data_type=model_name, page=page, count=count)


@main.route("/<model_name>/<int:instance_id>/changes/revert_change/<int:version>", methods=["GET", "POST"])
@login_required
def revert_change(model_name, instance_id, version):
    if model_name not in allowed_models:
        abort(404)
    model = get_class_by_tablename(model_name)
    instance = model.query.get_or_404(instance_id)
    instance.versions[version].revert()
    db.session.commit()
    flash('Successfully reverted changes', 'success')
    return redirect(url_for('main.index'))
