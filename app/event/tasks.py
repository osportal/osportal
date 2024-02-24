from app.celery import celery
from app.event.models import EventType


@celery.task()
def enable_event_type(ids):
    """
    Enable an event type.
    type ids: list
    return: int
    """
    return EventType.bulk_enable(ids)

@celery.task()
def disable_event_type(ids):
    """
    Disable an event type.
    type ids: list
    return: int
    """
    return EventType.bulk_disable(ids)

@celery.task()
def delete_event_type(ids):
    """
    Delete an event type.
    type ids: list
    return: int
    """
    return EventType.bulk_delete(ids)
