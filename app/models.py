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


class Company(ResourceMixin):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(65), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    sites = db.relationship('Site', backref='company', primaryjoin='Company.id==Site.company_id', lazy='select')

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Company.name.ilike(search_query),)

        return or_(*search_chain)


class Site(ResourceMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(200), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))

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
    holidays = db.relationship('PublicHoliday', backref='country',
                               primaryjoin='Country.id==PublicHoliday.country_id',
                               lazy='select')
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



class PublicHoliday(ResourceMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))

    def __repr__(self):
        return self.name

    def full_calendar_add_one_day(self):
        return self.start_date + datetime.timedelta(days=1)

    @property
    def year(self):
        return self.start_date.year

    @classmethod
    def unique_years_by_country(cls, cid):
        l = []
        c_holidays = PublicHoliday.query.filter(PublicHoliday.country_id==cid).all()
        for holiday in c_holidays:
            if holiday.year not in l:
                l.append(holiday.year)
        return sorted(l, reverse=True)

    @classmethod
    def filter_year(cls, year):
        return sqlalchemy.extract('year', PublicHoliday.start_date) == year
