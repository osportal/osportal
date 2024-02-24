from app.celery import celery
from app.posts.models import Post

@celery.task()
def unpin_post_task(id):
    """
    Unpin Posts
    type id: int
    return: int
    """
    unpin_count = 0
    post = Post.query.get(id)
    if post.is_pin:
        post.unpin()
        unpin_count += 1
    return unpin_count

@celery.task()
def pin_post_task(id):
    """
    Pin Posts
    type id: int
    return: int
    """
    pin_count = 0
    for post in Post.query.all():
        if post.is_pin: post.unpin()
    post = Post.query.get(id)
    post.pin()
    pin_count += 1
    return pin_count
