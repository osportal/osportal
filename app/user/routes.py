from app.admin.utils import get_settings_value
from app.extensions import db
from app.decorators import setup_required
from app.admin.models import Settings
from app.admin.forms import SearchForm
from app.posts.models import Post, Comment
from app.user.auth import auth_user_db
from app.user.decorators import (anonymous_required,
                                 registration_enabled
                                 )
from app.user.models import User, Notification
from app.user.utils import save_picture, delete_picture
from app.user.forms import (LoginForm, RegistrationForm, UpdateAccountForm,
                            ForgotPasswordForm, ResetPasswordForm, UpdateAccountForm)
from datetime import datetime
from flask import (render_template, request, url_for, redirect,
                   flash, abort, Blueprint, g, current_app, jsonify)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy import text


user = Blueprint('user', __name__, template_folder='./templates')


@user.before_request
@setup_required()
def before_request():
    pass


@user.route('/login', methods=['GET', 'POST'])
@anonymous_required()
def login():
    next_url = request.args.get('next')
    form = LoginForm()
    if form.validate_on_submit():
        next_url = request.form['next']
        user = auth_user_db(request.form.get('identity'), request.form.get('password'))
        if user:
            if user.active:
                login_user(user, remember=form.remember.data)
                user.update_login_activity(request.remote_addr)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for('main.index'))
            else:
                flash('This account has been disabled', 'danger')
        else:
            flash(f'Login Unsuccessful! Please check credentials', 'danger')
    return render_template('login.html', form=form)


@user.route('/register', methods=['GET', 'POST'])
@registration_enabled()
@anonymous_required()
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User()
    form = RegistrationForm()
    if form.validate_on_submit():
        form.populate_obj(user)
        user.password = User.encrypt_password(form.password.data)
        role = get_settings_value('reg_user_role')
        country = get_settings_value('reg_user_country')
        user.role = role
        user.country = country
        user.save()
        flash(f'User successfully registered', 'success')
        return redirect(url_for('user.login'))
    return render_template('register.html', form=form)


@user.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('user.login'))


@user.route('/forgotpassword', methods=['GET', 'POST'])
@anonymous_required()
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                from app.email import (send_password_reset_email)
                send_password_reset_email.delay(user)
            except Exception as e:
                flash(f'{e}', 'danger')
            else:
                flash('Check your email for instructions to reset your password', 'success')
                return redirect(url_for('user.login'))
    return render_template("forgot_password.html", form=form)


@user.route('/notifications', defaults={'page': 1}, methods=['GET', 'POST'])
@user.route('/notifications/page/<int:page>', methods=['GET', 'POST'])
@login_required
def notifications(page):
    current_user.last_notification_read_time = datetime.utcnow()
    db.session.commit() #commit being read, otherwise notification still appears
    notifications = current_user.notifications \
                    .order_by(Notification.created_at.desc()) \
                    .paginate(page, get_settings_value('items_per_admin_page'), True)
    return render_template('notifications.html', notifications=notifications)


@user.route('/notifications/recent', methods=['POST'])
@login_required
def recent_notifications():
    return str(current_user.new_notifications())


@user.route('/notification/<int:id>/delete', methods=['POST'])
@login_required
def delete_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.delete()
    flash(f'Your notification has been deleted', 'success')
    return redirect(url_for('user.notifications'))


@user.route('/notifications/delete', methods=['POST'])
@login_required
def delete_notifications():
    from app.user.tasks import delete_all_notifications
    delete_all_notifications.delay(current_user.id)
    flash(f'Your notifications are scheduled to be deleted', 'success')
    return redirect(url_for('user.notifications'))


@user.route('/notifications/bulk_delete', methods=['POST'])
def notifications_bulk_delete():
    if request.form.get('checked-items'):
        ids = request.form.get('checked-items').split(",")
        # stops circular import error
        from app.user.tasks import bulk_delete_notifications
        bulk_delete_notifications.delay(ids)
        flash('{0} notifications(s) scheduled to be deleted.'.format(len(ids)), 'success')
    else:
        flash('No items selected', 'danger')
    return redirect(url_for('user.notifications'))


@user.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm(obj=current_user)
    current_picture = current_user.image_file
    if form.validate_on_submit():
        form.populate_obj(current_user)
        if form.image_file.data:
            # delete existing picture
            if request.files['image_file']:
                delete_picture(current_picture)
                f = request.files['image_file']
                image = save_picture(f)
                current_user.image_file = image
        current_user.save()
        flash(f'Your account has been updated', 'success')
        return redirect(url_for('user.account'))
    return render_template('profile_settings.html', form=form)


@user.route('/users/get_list', methods=['GET'])
@login_required
def mentions():
    users = User.query.filter(User.active==True, User.id != current_user.id).all()
    return jsonify([user.serialize() for user in users])


@user.route('/user/<string:username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter(User.username==username).first_or_404()
    return render_template('profile.html', user=user)


@user.route('/user/<string:username>/posts', defaults={'page': 1}, methods=['GET', 'POST'])
@user.route('/user/<string:username>/posts/page/<int:page>', methods=['GET', 'POST'])
def posts(username, page):
    user = User.query.filter(User.username==username).first_or_404()
    paginated_posts = user.posts \
            .order_by(Post.created_at.desc()) \
            .paginate(page, get_settings_value('posts_per_page'), True)
    return render_template('profile_posts.html', posts=paginated_posts, user=user)


@user.route('/user/<string:username>/comments', defaults={'page': 1}, methods=['GET', 'POST'])
@user.route('/user/<string:username>/comments/page/<int:page>', methods=['GET', 'POST'])
def comments(username, page):
    user = User.query.filter(User.username==username).first_or_404()
    paginated_comments = user.comments \
            .order_by(Comment.created_at.desc()) \
            .paginate(page, get_settings_value('comments_per_page'), True)
    return render_template('profile_comments.html', page=page, comments=paginated_comments, user=user)


@user.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect('/')
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            # prevents circular import error
            from app.email import send_password_reset_email
            send_password_reset_email.delay(user)
            flash(f'An email has been sent with instructions to reset your password', 'info')
            return redirect(url_for('user.login'))
        except:
            return redirect(url_for('user.reset_request'))
    return render_template('reset_request.html', form=form)


@user.route('/password_reset/<token>', methods=['GET', 'POST'])
@anonymous_required()
def password_reset(token):
    user = User.verify_password_reset_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.password = User.encrypt_password(form.password.data)
            user.save()
            flash('Your password has been reset', 'success')
        except Exception as e:
            flash(e, 'danger')
        return redirect(url_for('user.login'))
    return render_template('reset_password.html', form=form, token=token)


@user.route('/users', defaults={'page': 1}, methods=['GET', 'POST'])
@user.route('/users/page/<int:page>', methods=['GET', 'POST'])
@login_required
def all_users(page):
    search_form = SearchForm()
    paginated_users = User.query \
        .filter(User.search((request.args.get('q', text(''))))) \
        .order_by(User.username.asc(),) \
        .paginate(page, get_settings_value('users_per_page'), True)
    return render_template('all_users.html', users=paginated_users, form=search_form)
