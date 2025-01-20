from app.celery import celery
from app.models import Entt, Site
from app.posts.models import Comment
from app.user.models import User, Role, Permission
from app.department.models import Department

from flask import url_for

@celery.task()
def send_welcome_email(ids):
    """
    Send user reset password email.
    type ids: list
    return: int
    """
    return User.bulk_send_welcome_email(ids)

@celery.task()
def reset_users_passwords(ids):
    """
    Send user reset password email.
    type ids: list
    return: int
    """
    return User.bulk_password_reset(ids)

@celery.task()
def update_entt(ids, entt):
    """
    Update user entitlement template
    type ids: list
    type entt: string id
    return: int
    """
    save_count = 0
    entt = Entt.query.get(int(entt))
    for id in ids:
        user = User.query.get(id)
        user.entt = entt
        user.save()
        save_count += 1
    return save_count

@celery.task()
def update_role(ids, role):
    """
    Update user role
    type ids: list
    type role: string id
    return: int
    """
    save_count = 0
    role = Role.query.get(int(role))
    for id in ids:
        user = User.query.get(id)
        user.role = role
        user.save()
        save_count += 1
    return save_count

@celery.task()
def update_site(ids, site):
    """
    Update user site
    type ids: list
    type site: string id
    return: int
    """
    save_count = 0
    site = Site.query.get(int(site))
    for id in ids:
        user = User.query.get(id)
        user.site = site
        user.save()
        save_count += 1
    return save_count

@celery.task()
def update_departments(ids, departments):
    """
    Update user departments
    type ids: list
    type departments: string id
    return: int
    """
    save_count = 0
    department_list = []
    for dept_id in departments:
        department = Department.query.get(dept_id)
        department_list.append(department)
    for id in ids:
        user = User.query.get(id)
        try:
            user.department = department_list
        except (ValueError, Exception) as e:
            print(e)
            continue
        else:
            user.save()
            save_count += 1
    return save_count

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
