from app.celery import celery
from app.pages.models import Page

@celery.task()
def delete_page(ids):
    """
    Delete a page.
    type ids: list
    return: int
    """
    return Page.bulk_delete(ids)

@celery.task()
def enable_page(ids):
    """
    Enable a page.
    type ids: list
    return: int
    """
    return Page.bulk_enable(ids)

@celery.task()
def disable_page(ids):
    """
    Disable a page.
    type ids: list
    return: int
    """
    return Page.bulk_disable(ids)

