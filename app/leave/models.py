from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin, StripStr
import datetime
from decimal import Decimal
from flask_continuum import VersioningMixin
from flask import current_app
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property


class LeaveType(ResourceMixin):
    __tablename__ = 'leave_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(30), unique=True, nullable=False)
    deductable = db.Column(db.Boolean, default=False, nullable=False)
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
    id = db.Column(db.Integer, primary_key=True) # used in import zip job
    leave_id = db.Column(db.Integer, db.ForeignKey('leave.id'), onupdate='CASCADE', nullable=False)
    authoriser_id = db.Column(db.Integer, db.ForeignKey('user.id'), onupdate='CASCADE', nullable=False)


class Leave(ResourceMixin, VersioningMixin):
    __tablename__ = 'leave'
    STATUS = ['Pending', 'Approved', 'Declined', 'Revoked']
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(*STATUS, name='status_types', native_enum=False),
                     index=True, nullable=False, server_default='Pending')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    half_day = db.Column(db.Boolean)
    duration = db.Column(db.Numeric(precision=6, scale=2), nullable=False)
    ltype_id = db.Column(db.Integer, db.ForeignKey('leave_type.id'), nullable=True)
    ltype = db.relationship('LeaveType', foreign_keys=[ltype_id])
    details = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    actioned_by = db.relationship('User',
                                  secondary='leave_actioned',
                                  backref='actioned_leaves',
                                  lazy='select',
                                  uselist=False)
    status_details = db.Column(db.String(120), nullable=True)
    time_unit = db.Column(
        db.Enum('days', 'hours', name='leave_time_unit', native_enum=False),
        nullable=False,
        server_default='days'
    )

    @hybrid_property
    def num_days(self):
        # https://stackoverflow.com/questions/19965018/python-decimal-checking-if-integer
        return self.user.entt.convert_entitlement(
            value=self.duration,
            unit=self.time_unit,  # Use leave's stored time unit
            target_unit='days',
            hours_per_day=self.user.entt.working_hours_per_day
        )

    def convert_to_int(self, value):
        # Check if the value is a Decimal and has no decimal part
        if isinstance(value, Decimal) and value % 1 == 0:
            return int(value)  # Convert to integer
        return value  # Return as is if there's a decimal part

    @hybrid_property
    def hex_colour(self):
        if self.status == 'Pending':
            return '#eb5009'
        return self.ltype.hex_colour

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

    def is_deductable(self):
        if self.ltype.deductable == True:
            # Determine the requested leave amount (consider half-day logic)
            #requested = 0.5 if leave.half_day else leave.days

            # User's entitlement time unit
            user_unit = self.user.entt.time_unit  # 'days' or 'hours'
            # Convert requested days to the user's entitlement unit if needed
            equivalent_amount = self.user.entt.convert_entitlement(
                value=self.duration,
                unit=self.time_unit,
                target_unit=user_unit
            )

            # Check if the user has enough entitlement remaining
            if equivalent_amount > self.user.entitlement_rem:
                raise Exception('User does not have enough allowance for this request')

            # Deduct the equivalent amount
            self.user.deduct_leave_days(equivalent_amount)

    def init_request(self):
        if self.ltype.approval == True:
            self.request_notification()
        elif self.ltype.approval == False:
            self.is_deductable()
            self.status_update('Approved')
