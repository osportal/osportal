from app.admin.utils import get_settings_value
from app.decorators import setup_required
from app.extensions import db
from app.posts.decorators import posts_enabled
from app.posts.forms import SearchForm, PostForm, CommentForm
from app.posts.models import Post, Comment
from app.user.decorators import permission_required

from elasticsearch_dsl import Search, Q
from flask import render_template, request, url_for, redirect, flash, abort, Blueprint, current_app
from flask_login import login_user, current_user, logout_user, login_required
import math
from sqlalchemy import text
from sqlalchemy.exc import PendingRollbackError, IntegrityError

posts = Blueprint('posts', __name__, template_folder='./templates')


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


@posts.route('/posts', defaults={'page': 1}, methods=['GET', 'POST'])
@posts.route('/posts/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.post', 'post', crud='read')
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
        .paginate(page, get_settings_value('posts_per_page'), True)
    return render_template('posts.html', posts=paginated_posts, pinned_posts=pinned_posts, form=form)


@posts.route('/posts/new', methods=['GET', 'POST'])
@permission_required('admin.post', 'post', crud='create')
def post_new():
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
            flash(f'Successfully created new post', 'success')
            return redirect(url_for('posts.index'))
    return render_template('edit.html', form=form)


@posts.route("/posts/<int:id>/edit", methods=['GET', 'POST'])
@permission_required('admin.post', 'post', crud='update')
def post_edit(id):
    post = Post.query.get_or_404(id)
    post.is_locked()
    if post.user_id != current_user.id:
        if not current_user.role.superuser and \
                not current_user.permission('admin.post', crud='update'):
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
    return render_template('edit.html', form=form, post=post)


@posts.route("/posts/<int:id>/delete", methods=['POST'])
@permission_required('admin.post', 'post', crud='delete')
def post_delete(id):
    post = Post.query.get_or_404(id)
    post.is_locked()
    # checks if non-author has admin permission to delete because
    # permission required does not prevent another user from accessing route
    if post.user != current_user:
        if not current_user.role.superuser and \
                current_user.permission('admin.post', crud='delete'):
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
@permission_required('admin.post', 'post', crud='read')
def post(id, page):
    post = Post.query.filter(Post.id==id).filter(Post.active).first_or_404()
    paginated_comments = post.paginated_comments(page)
    form = CommentForm()
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


@posts.route("/comments/<int:id>", methods=['GET', 'POST'])
def comment(id):
    comment = Comment.query.get_or_404(id)
    comment_in_post = Comment.query \
            .filter(Comment.post_id == comment.post_id, Comment.id >= comment.id) \
            .order_by(Comment.id.desc()).count()
    #NOTE if asc/desc is changed above, filter gt / lt has to be changed accordingly.
    #NOTE if above is changed, previous comment notifications will not work as expected.
    page = int(math.ceil(comment_in_post / float(get_settings_value('posts_per_page'))))
    url_kwargs = f'#cid{comment.id}'
    url = url_for('posts.post', id=comment.post_id, page=page) + url_kwargs
    return redirect(url)


@posts.route("/comments/<int:id>/edit", methods=['GET', 'POST'])
@permission_required('admin.comment', 'comment', crud='update')
def comment_edit(id):
    comment = Comment.query.get_or_404(id)
    # if post is locked, cannot edit comments
    post = Post.query.get_or_404(comment.post_id)
    if post.is_locked():
        return redirect(403)
    if comment.user_id != current_user.id:
        if not current_user.role.superuser and \
                not current_user.permission('admin.comment', crud='update'):
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
            flash(f'comment has been updated', 'success')
            redirect(url_for('posts.post', id=comment.post_id))
    return render_template('update_comment.html', comment=comment,
                           form=form)


@posts.route("/comments/<int:id>/delete", methods=['POST'])
@permission_required('admin.comment', 'comment', crud='delete')
def comment_delete(id):
    comment = Comment.query.get_or_404(id)
    # if post is locked, cannot delete comments
    post = Post.query.get_or_404(comment.post_id)
    post.is_locked()
    # checks if non-author has admin permission to delete because
    # permission required does not prevent another user from accessing route
    if comment.user_id != current_user.id:
        if not current_user.role.superuser and \
                not current_user.permission('admin.comment', crud='delete'):
                    abort(403)
    try:
        comment.delete()
    except (IntegrityError, PendingRollbackError) as e:
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash(f'comment has been deleted', 'success')
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
