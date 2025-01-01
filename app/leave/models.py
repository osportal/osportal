from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin, StripStr
import datetime
from flask_continuum import VersioningMixin
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property


class LeaveType(ResourceMixin):
    __tablename__ = 'leave_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(30), unique=True, nullable=False)
    deductable = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    approval = db.Column(db.Boolean, default=True, nullable=False)
    hex_colour = db.Column(StripStr(10), nullable=False, default='#0066FF')

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (LeaveType.name.ilike(search_query),)

        return or_(*search_chain)


class LeaveActioned(ResourceMixin):
    __tablename__ = 'leave_actioned'
    id = db.Column(db.Integer, nullable=True, unique=True) # used in import zip job
    leave_id = db.Column(db.Integer, db.ForeignKey('leave.id'), onupdate='CASCADE', primary_key=True)
    authoriser_id = db.Column(db.Integer, db.ForeignKey('user.id'), onupdate='CASCADE', primary_key=True)


class Leave(ResourceMixin, VersioningMixin):
    __tablename__ = 'leave'
    STATUS = ['Pending', 'Approved', 'Declined', 'Revoked']
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(*STATUS, name='status_types', native_enum=False),
                     index=True, nullable=False, server_default='Pending')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    half_day = db.Column(db.Boolean)
    days = db.Column(db.Numeric(precision=4, scale=1))
    ltype_id = db.Column(db.Integer, db.ForeignKey('leave_type.id'), nullable=True)
    ltype = db.relationship('LeaveType', foreign_keys=[ltype_id])
    details = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    actioned_by = db.relationship('User', secondary='leave_actioned', backref='actioned_leaves', lazy='select', uselist=False)
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
        else:
            return self.ltype.get_hex_colour()

    def full_calendar_add_one_day(self):
        return self.end_date + datetime.timedelta(days=1)

    def calculate_days(self):
        delta = self.full_calendar_add_one_day() - self.start_date
        return delta.days

    def status_update(self, new_status):
        self.status = new_status
        return self.save()

    def request_notification(self):
        from app.admin.utils import get_settings_value
        if get_settings_value('system_email_id'):
            from app.email import send_leave_request_email
            send_leave_request_email.delay(leave.id)

    def init_request(self):
        if self.ltype.approval == True:
            self.request_notification()
        elif self.ltype.approval == False:
            self.status_update('Approved')
