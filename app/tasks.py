from app.celery import celery
from app.extensions import db
from app.models import get_class_by_tablename, PublicHoliday, PublicHolidayGroup


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


@celery.task()
def bulk_copy_holidays_to_years(ids, years):
    """
    :param ids: list of publicHolidays ids to be copied
    :param years: list of selected years for new public holiday
    :type ids and years: list
    :return: int
    """
    copy_count = 0

    for id in ids:
        holiday = PublicHoliday.query.get(id)
        if holiday is None:
            continue
        else:
            for selected_year in years:
                try:
                    selected_year = int(selected_year)
                    new_start_date = holiday.start_date.replace(year=selected_year)
                except (ValueError, Exception) as e:
                    continue
                else:
                    new_holiday = PublicHoliday(
                        name=holiday.name,
                        start_date=new_start_date,
                        group_id=holiday.group_id
                    )
                    db.session.add(new_holiday)
                    copy_count += 1
    db.session.commit()
    return copy_count


@celery.task()
def bulk_copy_holidays_to_groups(ids, groups):
    """
    :param ids: list of publicHolidays ids to be copied
    :param years: list of selected groups
    :type ids and groups: list
    :return: int
    """
    copy_count = 0

    for id in ids:
        holiday = PublicHoliday.query.get(id)
        if holiday is None:
            continue
        else:
            for selected_group in groups:
                try:
                    group = PublicHolidayGroup.query.get(selected_group)
                except (ValueError, Exception) as e:
                    continue
                else:
                    new_holiday = PublicHoliday(
                        name=holiday.name,
                        start_date=holiday.start_date,
                        group_id=group.id
                    )
                    db.session.add(new_holiday)
                    copy_count += 1
    db.session.commit()
    return copy_count
