from app.extensions import db
from app.admin.utils import check_licence
from flask import Markup, abort, current_app
from sqlalchemy import func
from sqlalchemy.types import TypeDecorator

import datetime

class StripStr(TypeDecorator):
    """ White space at beginning and end of string is stripped (does NOT strip all spaces).
    """
    impl = db.String
    cache_ok=True

    def process_bind_param(self, value, dialect):
        # in case of multiple string values and pass None
        return value.strip() if value else value

    def copy(self, **kw):
        return StripStr(self.impl.length)


class FmtString(TypeDecorator):
    """ White space at beginning and end of string is stripped (does NOT strip all spaces).
    String is then formatted to lowercase
    """
    impl = db.String
    cache_ok=True

    def process_bind_param(self, value, dialect):
        # in case of multiple string values and pass None
        return value.strip().lower() if value else value

    def copy(self, **kw):
        return FmtString(self.impl.length)



class ResourceMixin(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    locked = db.Column(db.Boolean, default=False, nullable=True)

    def save(self):
        """
        Save model instance and
        return model instance
        """
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """
        Delete model instance and
        return result
        """
        db.session.delete(self)
        return db.session.commit()


    def fmt_date(self, date):
        if date:
            return date.strftime("%-d %b %Y")

    def render(self, value):
        if type(value) == bool:
            if value: # if its True
                rendered = '<span class="text-success"><i class="bi bi-check2 fa-lg"></i></span>'
            elif value is None:
                rendered = '<span class="text-muted">&mdash;</span>'
            else:
                # if False
                rendered = '<span class="text-danger"><i class="bi bi-x fa-lg"></i></span>'
            return Markup(rendered)

    @classmethod
    def bulk_delete(cls, ids):
        """
        :param ids: list of ids to be deleted
        :type ids: list
        :return: int
        """
        delete_count = 0

        for id in ids:
            obj = cls.query.get(id)
            if obj is None:
                continue
            else:
                if cls.__name__ == 'User':
                    if obj.is_last_superuser():
                        continue
                    if obj.locked:
                        continue
                db.session.delete(obj)
                delete_count += 1
        db.session.commit()
        return delete_count

    @classmethod
    def bulk_disable(cls, ids):
        disable_count = 0

        for id in ids:
            obj = cls.query.get(id)
            if obj is None:
                continue
            else:
                if cls.__name__ == 'User':
                    if obj.is_last_superuser():
                        continue
                    if obj.locked:
                        continue
                obj.active = False
                db.session.add(obj)
                disable_count += 1
        db.session.commit()
        return disable_count

    @classmethod
    def bulk_enable(cls, ids):
        enable_count = 0

        for id in ids:
            obj = cls.query.get(id)
            if obj is None:
                continue

            if cls.__name__ == 'User': # if cls is User
                if not obj.active: # only consider inactive objects that are to be enabled
                    check_licence(1)
            obj.active = True
            db.session.add(obj)
            enable_count += 1
        try:
            db.session.commit()
        except Exception as commit_error:
            print(f"DEBUG: Commit error: {commit_error}")
            db.session.rollback()
            raise

        return enable_count

    @classmethod
    def sort_by(cls, field, direction):
        if field not in cls.__table__.columns:
            field = 'created_at'

        if direction not in ('asc', 'desc'):
            direction = 'asc'

        return field, direction

    def is_locked(self):
        if self.locked:
            return abort(403)

    def pretty_date(self, time):
        """ if time is less than 24 hours pretty print timestamp
        e.g. just now, a minute ago, 1 hour ago, 7 hours ago etc """
        now = datetime.datetime.utcnow()
        # add replace as you can't subtract offset-naive and offset-aware datetimes
        diff = now - time.replace(tzinfo=None)
        second_diff = diff.seconds
        day_diff = diff.days
        if day_diff < 0:
            return ''
        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff // 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff // 3600) + " hours ago"
        if day_diff == 1:
            return str(day_diff) + " day ago"
        else:
            return str(day_diff) + " days ago"
