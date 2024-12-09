from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin, StripStr
import datetime
from sqlalchemy import or_
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


# Entitlement Template
class Entt(ResourceMixin):
    __tablename__ = 'entt'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(50), unique=True, nullable=False)
    description = db.Column(db.String(300), nullable=True)

    ph_group_id = db.Column(db.Integer,
                            db.ForeignKey('public_holiday_group.id'),
                            nullable=True)
    public_holiday_group = db.relationship("PublicHolidayGroup",
                                           foreign_keys=[ph_group_id])

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Entt.name.ilike(search_query),)

        return or_(*search_chain)



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
    default_annual_allowance = db.Column(db.Integer, nullable=True, default=25)#TODO need nullable changing to False
    max_carry_over_days = db.Column(db.Integer, nullable=True, default=10)

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
    description = db.Column(db.Text, nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    country = db.relationship("Country", foreign_keys=[country_id])
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
