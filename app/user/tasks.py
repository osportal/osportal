from app.celery import celery
from app.user.models import User, Role
from app.posts.models import Comment
from flask import url_for

@celery.task()
def delete_users(ids):
    """
    Delete users.
    type ids: list
    return: int
    """
    return User.bulk_delete(ids)


@celery.task()
def reset_users_passwords(ids):
    """
    Send user reset password email.
    type ids: list
    return: int
    """
    return User.bulk_password_reset(ids)

@celery.task()
def disable_user_login(ids):
    """
    Disable user login
    type ids: list
    return: int
    """
    return User.bulk_disable_login(ids)

@celery.task()
def enable_user_login(ids):
    """
    Re-enable user login
    type ids: list
    return: int
    """
    return User.bulk_enable_login(ids)


@celery.task()
def new_comment_notification(id):
    comment = Comment.query.get(id)
    endpoint = url_for('posts.post', id=comment.post_id) + '#cid' + str(comment.id)
    html = f'''{comment.user.username} commented on your post: {comment.parent}'''
    comment.parent.user.add_notification(html, endpoint)



@celery.task()
def user_mentions(obj, ids, *args):
    """
    Check if users are mentioned in posts/comments
    type ids: object
    return: int
    """
    tablename = obj.__table__.name
    limit = 44
    mention_count = 0
    for id in ids:
        user = User.query.get(id)
        if user is None:
            continue
        else:
            mention_count += 1
            if tablename == 'post':
                post = Post.query.get(obj.id)
                endpoint = url_for('posts.post', id=post.id)
                html = f'''{post.user.username} mentioned you in a post: {post.name}'''
            elif tablename == 'comment':
                comment = Comment.query.get(obj.id)
                endpoint = url_for('posts.post', id=comment.post_id) + '#cid' + str(comment.id)
                html = f'''{comment.user.username} mentioned you in a comment on the post: {args[0][0]}'''
            user.add_notification(html, endpoint)
    return mention_count


@celery.task()
def delete_all_notifications(user_id):
    """
    Delete all notifications.
    type ids: object
    return: int
    """
    user = User.query.get(user_id)
    return user.delete_all_notifications()

@celery.task()
def bulk_delete_notifications(ids):
    """
    Delete selected notifications.
    type ids: list
    return: int
    """
    return User.bulk_delete_notifications(ids)

@celery.task()
def delete_roles(ids):
    """
    Delete roles.
    type ids: list
    return: int
    """
    return Role.bulk_delete(ids)
