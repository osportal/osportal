from app.admin.utils import get_settings_value
from app.decorators import setup_required
from app.extensions import db
from app.posts.decorators import posts_enabled
from app.posts.forms import SearchForm, PostForm, CommentForm
from app.posts.models import Post, Comment
from app.user.decorators import permission_required
from app.utils.storage import upload_folder

from elasticsearch_dsl import Search, Q
from flask import (render_template,
                   request, url_for,
                   redirect,
                   flash,
                   abort,
                   Blueprint,
                   current_app,
                   send_from_directory,
                   Response,
                   jsonify)
from flask_login import login_user, current_user, logout_user, login_required
import math
import os
from pathlib import Path
import secrets
from sqlalchemy import text
from sqlalchemy.exc import PendingRollbackError, IntegrityError

posts = Blueprint('posts', __name__, template_folder='templates')


@posts.before_request
@setup_required()
@login_required
def before_request():
    """
    Protect all post endpoints
    with login_required
    """
    pass


def user_mentions_notification(obj, *args):
    if request.form.get('user-mentions'):
        ids = request.form.get('user-mentions').split(',')
        from app.user.tasks import user_mentions
        user_mentions.delay(obj, ids, args)


@posts.route('/', defaults={'page': 1}, methods=['GET', 'POST'])
@posts.route('/page/<int:page>', methods=['GET', 'POST'])
def index(page):
    form = SearchForm()
    pinned_posts = Post.query.filter(Post.is_pin==True).all()
    sort_by = Post.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
    paginated_posts = Post.query \
        .filter(Post.active) \
        .filter(Post.search((request.args.get('q', text(''))))) \
        .order_by(Post.is_pin.desc(), text(order_values)) \
        .paginate(page, 30, True)
    return render_template('posts.html', posts=paginated_posts, pinned_posts=pinned_posts, form=form)


@posts.route('/posts/new', methods=['GET', 'POST'])
def post_new():
    if not current_user.can_permission('can_create_posts'):
        if not current_user.permission('admin.post', crud='create'):
            abort(403)
    post = Post()
    form = PostForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(post)
            post.user_id = current_user.id
            post.save()
            #post.user.add_notification('unread_message_count', post.user.new_mention(post))
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            user_mentions_notification(post)
            flash(f'Created post', 'success')
            return redirect(url_for('posts.index'))
    return render_template('edit_post.html', form=form)


@posts.route("/posts/<int:id>/edit", methods=['GET', 'POST'])
def post_edit(id):
    post = Post.query.get_or_404(id)
    post.is_locked()
    if (post.user_id != current_user.id) or ((post.user == current_user) and not current_user.can_permission('can_edit_posts')):
        if not current_user.permission('admin.post', crud='update'):
            abort(403)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        try:
            form.populate_obj(post)
            post.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            user_mentions_notification(post)
            flash(f'Updated post', 'success')
            return redirect(url_for('posts.post', id=post.id))
    return render_template('edit_post.html', form=form, post=post)


@posts.route("/posts/<int:id>/delete", methods=['POST'])
def post_delete(id):
    post = Post.query.get_or_404(id)
    post.is_locked()
    # checks if non-author has admin permission to delete because
    # permission required does not prevent another user from accessing route
    if (post.user_id != current_user.id) or ((post.user == current_user) and not current_user.can_permission('can_delete_posts')): # can this user delete personal posts
        if not current_user.permission('admin.post', crud='delete'):
            abort(403)
    try:
        post.delete()
    except (IntegrityError, PendingRollbackError) as e:
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash(f'Deleted post', 'success')
    return redirect(url_for('posts.index'))


@posts.route("/posts/<int:id>", defaults={'page': 1}, methods=['GET', 'POST'])
@posts.route("/posts/<int:id>/page/<int:page>", methods=['GET', 'POST'])
def post(id, page):
    post = Post.query.filter(Post.id==id).filter(Post.active).first_or_404()
    paginated_comments = post.paginated_comments(page)
    if current_user.permission('admin.comment', crud='create') or current_user.can_permission('can_create_comments'):
        form = CommentForm()
        form.text.label.text = 'Your comment'
        # TODO check if user has permission to create comment
        # if current_user.permission('create_comments'):
        if form.validate_on_submit():
            comment = Comment()
            # do not allow new comments on locked posts
            post.is_locked()
            form.populate_obj(comment)
            comment.post_id=post.id
            comment.user_id=current_user.id
            comment.save()
            from app.user.tasks import new_comment_notification
            # TODO fix to use the object instead of int - investigate why it works elsewhere
            if comment.user_id != post.user_id:
                new_comment_notification.delay(int(comment.id))
            user_mentions_notification(comment, post.name)
            flash(f'Successfully posted', 'success')
            return redirect(url_for('posts.post', id=post.id))
        return render_template('post.html', post=post, comments=paginated_comments, form=form)
    else:
        return render_template('post.html', post=post, comments=paginated_comments)


@posts.route("/comments/<int:id>", methods=['GET', 'POST'])
def comment(id):
    comment = Comment.query.get_or_404(id)
    comment_in_post = Comment.query \
            .filter(Comment.post_id == comment.post_id, Comment.id >= comment.id) \
            .order_by(Comment.id.desc()).count()
    #NOTE if asc/desc is changed above, filter gt / lt has to be changed accordingly.
    #NOTE if above is changed, previous comment notifications will not work as expected.
    page = int(math.ceil(comment_in_post / float(30)))
    url_kwargs = f'#cid{comment.id}'
    url = url_for('posts.post', id=comment.post_id, page=page) + url_kwargs
    return redirect(url)


@posts.route("/comments/<int:id>/edit", methods=['GET', 'POST'])
def comment_edit(id):
    comment = Comment.query.get_or_404(id)
    # if post is locked, cannot edit comments
    post = Post.query.get_or_404(comment.post_id)
    if post.is_locked():
        return redirect(403)
    if (comment.user_id != current_user.id) or ((comment.user == current_user) and not current_user.can_permission('can_edit_comments')):
        if not current_user.permission('admin.comment', crud='update'):
            abort(403)
    form = CommentForm(obj=comment)
    if form.validate_on_submit():
        try:
            form.populate_obj(comment)
            comment.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            user_mentions_notification(comment)
            flash(f'Updated comment', 'success')
            redirect(url_for('posts.post', id=comment.post_id))
    return render_template('update_comment.html', comment=comment,
                           form=form)


@posts.route("/comments/<int:id>/delete", methods=['POST'])
def comment_delete(id):
    comment = Comment.query.get_or_404(id)
    # if post is locked, cannot delete comments
    post = Post.query.get_or_404(comment.post_id)
    post.is_locked()
    # checks if non-author has admin permission to delete because
    # permission required does not prevent another user from accessing route
    if (comment.user_id != current_user.id) or ((comment.user == current_user) and not current_user.can_permission('can_delete_comments')):
        if not current_user.permission('admin.comment', crud='delete'):
            abort(403)
    try:
        comment.delete()
    except (IntegrityError, PendingRollbackError) as e:
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash(f'Deleted comment', 'success')
    return redirect(url_for('posts.post', id=comment.post_id))


@posts.route("/posts/<int:id>/pin", methods=['GET', 'POST'])
@permission_required('admin.post', crud='update')
def pin_post(id):
    post = Post.query.get_or_404(id)
    print("POST", post)
    try:
        post.pin()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash('Pinned post', 'success')
    return redirect(url_for('posts.index'))


@posts.route("/posts/<int:id>/unpin", methods=['GET', 'POST'])
@permission_required('admin.post', crud='update')
def unpin_post(id):
    post = Post.query.get_or_404(id)
    try:
        post.unpin()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash('Unpinned post', 'success')
    return redirect(url_for('posts.index'))


@posts.route('/media/<path:filename>')
def get_uploaded_img(filename):
    path = Path(os.path.join(upload_folder(), 'media'))
    return send_from_directory(path, filename)


@posts.route("/upload-post-img", methods=['POST'])
def upload_image():
    f = request.files['upload']
    f.seek(0, os.SEEK_END)
    size = f.tell()
    max_upload_bytes = 15 * 1024 * 1024
    if size > max_upload_bytes:
        return Response(
        response='File size should be less than 15MB',
        status=413,
        )
    else:
        #seek back to image beginning, so you might save it entirely
        f.seek(0)
        random_hex = secrets.token_hex(24)
        _, f_ext = os.path.splitext(f.filename)
        new_fn = random_hex + f_ext
        path = Path(upload_folder(), 'media')
        path.mkdir(parents=True, exist_ok=True)
        f.save(os.path.join(path, new_fn))
        url = url_for('posts.get_uploaded_img', filename=new_fn)
        return jsonify(url=url)
