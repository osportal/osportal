from app.celery import celery
from app.models import get_class_by_tablename


@celery.task()
def delete_obj(table, ids):
    """
    Delete objs
    type ids: list
    return: int
    """
    class_name = get_class_by_tablename(table)
    return class_name.bulk_delete(ids)


@celery.task()
def disable_obj(table, ids):
    """
    Disable objs
    type ids: list
    return: int
    """
    class_name = get_class_by_tablename(table)
    return class_name.bulk_disable(ids)


@celery.task()
def enable_obj(table, ids):
    """
    Enable objs
    type ids: list
    return: int
    """
    class_name = get_class_by_tablename(table)
    return class_name.bulk_enable(ids)
