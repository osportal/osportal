from app.celery import celery
from app.models import Country, PublicHoliday

@celery.task()
def delete_holidays(ids):
    """
    Delete holidays.
    type ids: list
    return: int
    """
    return PublicHoliday.bulk_delete(ids)

@celery.task()
def delete_countries(ids):
    """
    Delete countries.
    type ids: list
    return: int
    """
    return Country.bulk_delete(ids)
