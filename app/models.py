from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin, StripStr
from app.leave.models import LeaveType
from collections import OrderedDict
import datetime
from flask import request
from sqlalchemy import or_, text, extract
from sqlalchemy.ext.hybrid import hybrid_property
import sqlalchemy


def get_class_by_tablename(tablename):
    """Return class reference mapped to table.
    https://stackoverflow.com/a/66666783

    :param tablename: String with name of table.
    :return: Class reference or None.
    """
    classes = []
    for m in db.Model.registry.mappers:
        c = m.class_
        if hasattr(c, "__tablename__") and c.__tablename__ == tablename:
            classes.append(c)

    # We didn't find this class
    if len(classes) == 0:
        return None
    # This is a class where we have only one possible candidate.
    # It's either a top level class or a polymorphic class with a specific hardcoded table name
    elif len(classes) == 1:
        return classes[0]
    # In this case we are dealing with a polymorphic table where all of the tables have the same table name.
    # However for us to identify the parent class we can look for the class that defines the polymorphic_on arg
    else:
        for c in classes:
            mapper_args = dict(c.__mapper_args__)
            if mapper_args.get("polymorphic_on") is not None:
                return c


class EnttLeaveTypes(ResourceMixin):
    __tablename__ = 'entt_leave_types'
    id = db.Column(db.Integer, unique=True) # used in import zip job
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_type.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                                index=True, primary_key=True)
    entt_id = db.Column(db.Integer,
                        db.ForeignKey('entt.id',
                                      onupdate='CASCADE',
                                      ondelete='CASCADE'),
                        index=True, primary_key=True)

    def __repr__(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return f'{leave_type.name}'

    def get_deductable(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.deductable

    def get_approval(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.approval

    def get_max_days(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.max_days

    def get_hex_colour(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.hex_colour

    @hybrid_property
    def lt_id(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.id

    @hybrid_property
    def name(self):
        leave_type = LeaveType.query.get(self.leave_type_id)
        return leave_type.name


# Entitlement Template
class Entt(ResourceMixin):
    __tablename__ = 'entt'
    UNIT = OrderedDict([
        ('days', 'Days'),
        ('hours', 'Hours')
        ])
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(50), unique=True, nullable=False)
    description = db.Column(db.String(300), nullable=True)
    default_entitlement = db.Column(db.Numeric(precision=6, scale=2), nullable=False, default=0)
    working_hours_per_day = db.Column(db.Numeric(precision=6, scale=2), nullable=True, default=8)
    entitlement_cap = db.Column(db.Numeric(precision=6, scale=2), nullable=False, default=0)
    max_carryover = db.Column(db.Numeric(precision=6, scale=2), nullable=False, default=0)

    weekend = db.Column(db.Boolean, nullable=False, default=False)
    half_day = db.Column(db.Boolean, nullable=False, default=True)
    time_unit = db.Column(db.Enum(*UNIT, name='role_types', native_enum=False),
                          index=True, nullable=False, server_default='days')

    ph_group_id = db.Column(db.Integer,
                            db.ForeignKey('public_holiday_group.id'),
                            nullable=True)
    public_holiday_group = db.relationship("PublicHolidayGroup",
                                           foreign_keys=[ph_group_id])
    leave_types = db.relationship('LeaveType', secondary='entt_leave_types',
                                    backref='entt', lazy='dynamic', uselist=True)

    def __repr__(self):
        return self.name

    def get_phg_colour(self):
        if self.public_holiday_group:
            return self.public_holiday_group.colour

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Entt.name.ilike(search_query),)

        return or_(*search_chain)

    def paginated_holidays(self, page):
        current_year = datetime.datetime.now().year
        sort_by = PublicHoliday.sort_by(request.args.get('sort', 'start_date'),
                               request.args.get('direction', 'desc'))
        order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
        holidays = PublicHoliday.query \
                .filter(PublicHoliday.group_id==self.ph_group_id) \
                .filter(extract('year', PublicHoliday.start_date) == current_year) \
                .order_by(text(order_values)) \
                .paginate(page, 15, False)
        return holidays


    def convert_entitlement(self, value, unit, target_unit, hours_per_day=8):
        # if entt does not have a working_hours_per_day value, default to 8
        if self.working_hours_per_day:
            hours_per_day = self.working_hours_per_day
        if unit == target_unit:
            return value
        if unit == 'days' and target_unit == 'hours':
            return value * hours_per_day
        if unit == 'hours' and target_unit == 'days':
            return value / hours_per_day
        raise ValueError("Unsupported unit conversion")


class Site(ResourceMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(200), nullable=False)

    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=True)
    country = db.relationship("Country", foreign_keys=[country_id])

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Site.name.ilike(search_query),)

        return or_(*search_chain)


class Country(ResourceMixin):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(StripStr(5), unique=True)
    name = db.Column(StripStr(100), unique=True, nullable=False)

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Country.name.ilike(search_query),
                        Country.code.ilike(search_query))

        return or_(*search_chain)


class PublicHolidayGroup(ResourceMixin):
    __tablename__ = "public_holiday_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    country = db.relationship("Country", foreign_keys=[country_id])
    colour = db.Column(db.String(10), nullable=False, default='#e10078')
    holidays = db.relationship('PublicHoliday', backref='group',
                               primaryjoin='PublicHolidayGroup.id==PublicHoliday.group_id',
                               cascade='delete',
                               lazy='select')

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (PublicHolidayGroup.name.ilike(search_query),)

        return or_(*search_chain)


class PublicHoliday(ResourceMixin):
    __tablename__ = "public_holiday"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('public_holiday_group.id'))

    def __repr__(self):
        return self.name

    def full_calendar_add_one_day(self):
        return self.start_date + datetime.timedelta(days=1)

    @property
    def year(self):
        return self.start_date.year

    @classmethod
    def unique_years_by_group(cls, gid):
        l = []
        query = PublicHoliday.query.filter(PublicHoliday.group_id==gid).all()
        for holiday in query:
            if holiday.year not in l:
                l.append(holiday.year)
        return sorted(l, reverse=True)

    @classmethod
    def filter_year(cls, year):
        return sqlalchemy.extract('year', PublicHoliday.start_date) == year
