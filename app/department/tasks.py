from app.celery import celery
from app.department.models import Department


@celery.task()
def delete_departments(ids):
    """
    Delete departments.
    type ids: list
    return: int
    """
    return Department.bulk_delete(ids)
