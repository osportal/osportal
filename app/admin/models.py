from app.models import Country
from app.department.models import Department
from app.event.models import EventType
from app.pages.models import Page
from app.posts.models import Post
from app.user.models import db, User, Role, Permission
from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from sqlalchemy import func, or_, event


class SystemEmail(ResourceMixin):
    __tablename__ = 'system_email'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(50), nullable=False)
    email = db.Column(FmtString(120), unique=True, nullable=False)
    server = db.Column(FmtString(120))
    port = db.Column(db.Integer)
    ssl = db.Column(db.Boolean, default=False) # SSL/TLS
    starttls = db.Column(db.Boolean, default=False)
    auth = db.Column(db.Boolean, default=False)
    username = db.Column(StripStr(120))
    password = db.Column(db.String(128), server_default='')

    def __repr__(self):
        return f'{self.name} <{self.email}>'

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (SystemEmail.name.ilike(search_query),)

        return or_(*search_chain)



class Settings(ResourceMixin):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    setup = db.Column(db.Boolean, default=True, nullable=False)
    site_name = db.Column(db.String(25), nullable=False)
    company_name = db.Column(db.String(30), nullable=True)
    company_website = db.Column(db.String(40), nullable=True)

    # Calendar
    weekend = db.Column(db.Boolean, nullable=False, default=False)#TODO change nullable=False
    half_day = db.Column(db.Boolean, nullable=False, default=True)#TODO change nullable=False
    pending_colour = db.Column(StripStr(10), nullable=False, default='#ffbf00')#TODO change nullable=False
    declined_colour = db.Column(StripStr(10), nullable=False, default='#000000')#TODO change nullable=False
    public_holiday_colour = db.Column(StripStr(10), nullable=False, default='#e10078')#TODO change nullable=False

    # Pagination
    items_per_admin_page = db.Column(db.Integer, nullable=False, default=50)
    posts_per_page = db.Column(db.Integer, nullable=False, default=25)
    comments_per_page = db.Column(db.Integer, nullable=False, default=25)
    users_per_page = db.Column(db.Integer, nullable=False, default=25)
    departments_per_page = db.Column(db.Integer, nullable=False, default=25)
    notifications_per_page = db.Column(db.Integer, nullable=False, default=25)
    events_per_page = db.Column(db.Integer, nullable=False, default=25)

    # Auth
    auth_type = db.Column(db.String(20), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    reg_user_role = db.relationship('Role', foreign_keys=[role_id], backref='settings')
    reg_user_country = db.relationship('Country', foreign_keys=[country_id], backref='settings')
    user_registration = db.Column(db.Boolean, nullable=True, default=False)

    #Email
    alert_email_id = db.Column(db.Integer, db.ForeignKey('system_email.id'), nullable=True)
    system_email_id = db.Column(db.Integer, db.ForeignKey('system_email.id'), nullable=True)

    # relationships
    system_email = db.relationship('SystemEmail', foreign_keys=[system_email_id], backref='system_email_ref', uselist=False)
    alert_email = db.relationship('SystemEmail', foreign_keys=[alert_email_id], backref='alert_email_ref', uselist=False)

    #LDAP
    #TODO ldap will be migrated to plugin system
    #ldap_host = db.Column(StripStr(500), nullable=True)
    #ldap_port = db.Column(db.Integer, nullable=True)
    #active_directory = db.Column(db.Boolean, nullable=True)
    #domain_name = db.Column(db.String(64), nullable=True)
    #ldap_bind_username = db.Column(StripStr(128), nullable=True)
    #ldap_bind_password = db.Column(StripStr(128), nullable=True)
    #ldap_search = db.Column(StripStr(500), nullable=True)
    #ldap_uid_field = db.Column(StripStr(500), nullable=True)
    #ldap_user_registration = db.Column(db.Boolean, nullable=True, default=False)
    #ldap_firstname_field = db.Column(StripStr(500), nullable=True)
    #ldap_lastname_field = db.Column(StripStr(500), nullable=True)
    #ldap_email_field = db.Column(StripStr(500), nullable=True)



class Dashboard(object):
    @classmethod
    def group_and_count_users(cls):
        return Dashboard._group_and_count(User, User.role)

    @classmethod
    def group_and_count_roles(cls):
        return Dashboard._group_and_count(Role, Role.name)

    @classmethod
    def group_and_count_permissions(cls):
        return Dashboard._group_and_count(Permission, Permission.db_name)

    @classmethod
    def group_and_count_departments(cls):
        return Dashboard._group_and_count(Department, Department.name)

    @classmethod
    def group_and_count_event_types(cls):
        return Dashboard._group_and_count(EventType, EventType.active)

    @classmethod
    def group_and_count_pages(cls):
        return Dashboard._group_and_count(Page, Page.active)

    @classmethod
    def group_and_count_posts(cls):
        return Dashboard._group_and_count(Post, Post.name)

    @classmethod
    def group_and_count_emails(cls):
        return Dashboard._group_and_count(SystemEmail, SystemEmail.name)

    @classmethod
    def group_and_count_countries(cls):
        return Dashboard._group_and_count(Country, Country.name)

    @classmethod
    def _group_and_count(cls, model, field):
        count = func.count(field)
        query = db.session.query(count, field).group_by(field).all()

        results = {
                'query': query,
                'total': model.query.count()
                }
        return results
