from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin, StripStr
import datetime
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property

class EventType(ResourceMixin):
    __tablename__ = 'event_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(30), unique=True, nullable=False)
    deductable = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    approval = db.Column(db.Boolean, default=True, nullable=False)
    hex_colour = db.Column(StripStr(10), nullable=False, default='#0066FF')
    max_days = db.Column(db.Integer, nullable=True, default=14)

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (EventType.name.ilike(search_query),)

        return or_(*search_chain)


class EventActioned(ResourceMixin):
    __tablename__ = 'event_actioned'
    id = db.Column(db.Integer, nullable=True) # used in import zip job
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), onupdate='CASCADE', primary_key=True)
    authoriser_id = db.Column(db.Integer, db.ForeignKey('user.id'), onupdate='CASCADE', primary_key=True)


class Event(ResourceMixin):
    STATUS = ['Pending', 'Approved', 'Declined', 'Revoked']
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(*STATUS, name='status_types', native_enum=False),
                     index=True, nullable=False, server_default='Pending')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    half_day = db.Column(db.Boolean)
    days = db.Column(db.Numeric(precision=4, scale=1))
    etype_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=True)
    etype = db.relationship('EventType', foreign_keys=[etype_id])
    details = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    actioned_by = db.relationship('User', secondary='event_actioned', backref='actioned_events', lazy='select', uselist=False)
    status_details = db.Column(db.String(120), nullable=True)

    @hybrid_property
    def num_days(self):
        # https://stackoverflow.com/questions/19965018/python-decimal-checking-if-integer
        if self.days.as_integer_ratio()[1] == 1:
            return int(self.days)
        return self.days

    @hybrid_property
    def hex_colour(self):
        #avoid circular import
        from app.admin.utils import get_settings_value
        if self.status == 'Pending':
            return get_settings_value('pending_colour')
        elif self.status == 'Declined':
            return '#000000'
            return get_settings_value('declined_colour')
        else:
            return self.etype.hex_colour

    def full_calendar_add_one_day(self):
        return self.end_date + datetime.timedelta(days=1)

    def calculate_days(self):
        delta = self.full_calendar_add_one_day() - self.start_date
        return delta.days

    @classmethod
    def initialize_event_request(cls, event):
        if event.etype.approval == True:
            from app.email import send_event_request_email
            send_event_request_email.delay(event.id)
        elif event.etype.approval == False:
            event.status = 'Approved'
            return event.save()
