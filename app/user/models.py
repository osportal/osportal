from app.admin.utils import get_settings_value
from app.extensions import db
from app.models import get_class_by_tablename
from app.event.models import Event
from app.posts.models import Comment
from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import UserMixin, logout_user, current_user
from flask import url_for, current_app, request
import json
import jwt
import os
from sqlalchemy import text, or_, func
from sqlalchemy.ext.hybrid import hybrid_property
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


class RolePermission(ResourceMixin):
    __tablename__ = "role_permission"
    id = db.Column(db.Integer, nullable=True) # used in import zip job
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, primary_key=True)
    role_id = db.Column(db.Integer,
                              db.ForeignKey('role.id',
                                            onupdate='CASCADE',
                                            ondelete='CASCADE'),
                              index=True, primary_key=True)


class Permission(ResourceMixin):
    __tablename__ = "permission"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(60), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=True)
    db_name = db.Column(StripStr(60), nullable=False)
    # CRUD
    create = db.Column(db.Boolean, default=False)
    read = db.Column(db.Boolean, default=False)
    update = db.Column(db.Boolean, default=False)
    delete = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'{self.name} <{self.db_name}>'

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Permission.name.ilike(search_query),)

        return or_(*search_chain)


class Role(ResourceMixin):
    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(50), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=True)
    # Superuser level permissions override any of the permissions
    superuser = db.Column(db.Boolean, default=False)

    # Permissions
    # posts and comment Permissions
    can_create_posts = db.Column(db.Boolean, nullable=True, default=True)
    can_edit_posts = db.Column(db.Boolean, nullable=True, default=True)
    can_delete_posts = db.Column(db.Boolean, nullable=True, default=True)
    can_create_comments = db.Column(db.Boolean, nullable=True, default=True)
    can_edit_comments = db.Column(db.Boolean, nullable=True, default=True)
    can_delete_comments = db.Column(db.Boolean, nullable=True, default=True)

    # editable user profile fields
    user_edit_email = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_username = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_image_file = db.Column(db.Boolean, nullable=True, default=True)
    user_edit_bio = db.Column(db.Boolean, nullable=True, default=True)

    permissions = db.relationship('Permission',
                                  secondary='role_permission',
                                  backref='permission_role',
                                  lazy='dynamic',
                                  uselist=True)


    def __repr__(self):
        return f"{self.name}"

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Role.name.ilike(search_query),)

        return or_(*search_chain)


    def check_permissions(self, permission):
        return getattr(self, permission)


    def check_admin_dash_access(self):
        if self.superuser:
            return self.superuser
        for p in self.permissions:
            if p.db_name[:5] == 'admin':
                return getattr(p, 'read')


    def check_admin_access(self, obj_type, access_level):
        # if user is superuser no need to check for any other permission
        if self.superuser:
            return self.superuser
        if self.permissions:
            for p in self.permissions:
                for obj in obj_type:
                    if p.db_name == obj:
                        return getattr(p, access_level)



class User(UserMixin, ResourceMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    dn = db.Column(db.String(50), nullable=True)
    username = db.Column(FmtString(113), unique=True, nullable=False)
    email = db.Column(FmtString(120), unique=True, nullable=False)
    contact_number = db.Column(db.String(25), unique=False, nullable=True)
    image_file = db.Column(db.String(40), nullable=True, default=None)
    password = db.Column(db.String(128), nullable=False, server_default='')
    active = db.Column(db.Boolean, default=True)
    hidden = db.Column(db.Boolean, nullable=False, default=False)
    dob = db.Column(db.DateTime, nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)

    last_notification_read_time = db.Column(db.DateTime)

    # Work
    job_title = db.Column(StripStr(100))
    authoriser_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    start_date = db.Column(db.Date, nullable=True)

    # Login Info
    current_login_time = db.Column(db.DateTime, default=datetime.utcnow())
    current_login_ip_address = db.Column(db.String(50))
    previous_login_time = db.Column(db.DateTime, default=datetime.utcnow())
    previous_login_ip_address = db.Column(db.String(50))

    # Leave Days
    leave_year_start = db.Column(db.Date, default=datetime.now().date().replace(month=1, day=1))
    annual_entitlement = db.Column(db.Numeric(precision=4, scale=1), default=0)
    used_days = db.Column(db.Numeric(precision=4, scale=1), default=0)
    days_left = db.Column(db.Numeric(precision=4, scale=1), default=0)
    carry_over_days = db.Column(db.Numeric(precision=4, scale=1), default=0)
    #total_holiday_entitlement = db.Column(db.Numeric(precision=4, scale=1), default=0)
    #max_carry_over_days = db.Column(db.Numeric(precision=4, scale=1), default=0)

    # RELATIONSHIPS
    role = db.relationship("Role", foreign_keys=[role_id], backref='user')
    authoriser = db.relationship(lambda: User,
                                 remote_side=id,
                                 backref=db.backref('lauthoriser', lazy='dynamic')
                                 )
    events = db.relationship('Event',
                             backref='user',
                             cascade='delete',
                             lazy=True)
    posts = db.relationship('Post',
                            backref='user',
                            primaryjoin='User.id==Post.user_id',
                            cascade='delete',
                            lazy='dynamic')
    comments = db.relationship('Comment',
                               backref='user',
                               primaryjoin='User.id==Comment.user_id',
                               cascade='delete',
                               lazy='dynamic')
    notifications = db.relationship('Notification',
                                    backref='user',
                                    cascade='delete',
                                    lazy='dynamic')
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    country = db.relationship('Country', foreign_keys=[country_id], backref='user')

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    company = db.relationship('Company', foreign_keys=[company_id], backref='user')

    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))
    site = db.relationship('Site', foreign_keys=[site_id], backref='user')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = User.encrypt_password(kwargs.get('password', ''))
        #self.annual_entitlement = self.country.default_annual_allowance
        self.days_left = self.annual_entitlement


    def __repr__(self):
        return self.username

    def __str__(self):
        return self.username + f' ({self.email})'


    def can_permission(self, permission):
        if self.role:
            access = self.role.check_permissions(permission)
            return access

    # admin permission
    def permission(self, *obj, crud):
        if self.role:
            access = self.role.check_admin_access(obj, crud)
            return access

    def post_actions_access(self, post):
        if self.role:
            return (post.user==self and (current_user.can_permission('can_edit_posts') or current_user.can_permission('can_delete_posts'))) or \
                   self.permission('admin.post', crud='delete') or \
                   self.permission('admin.post', crud='update')

    def comment_actions_access(self, comment):
        if self.role:
            return (comment.user==self and (current_user.can_permission('can_edit_comments') or current_user.can_permission('can_delete_comments'))) or \
                   (comment.user != self and current_user.can_permission('can_create_comments')) or \
                   self.permission('admin.comment', crud='delete') or \
                   self.permission('admin.comment', crud='update')


    @classmethod
    def calculate_tenure(cls, start_date):
        today = datetime.today()

        # Calculate the difference using relativedelta
        difference = relativedelta(today, start_date)

        # Extract years, months, and days from the difference
        years = difference.years
        months = difference.months
        days = difference.days

        # Build a result string, only including non-zero values
        parts = []
        if difference.years > 0:
            parts.append(f"{difference.years} year(s)")
        if difference.months > 0:
            parts.append(f"{difference.months} month(s)")
        if difference.days > 0:
            parts.append(f"{difference.days} day(s)")

        # Join the non-zero parts with commas
        result = ', '.join(parts)
        return result


    @classmethod
    def calculate_age(cls, dob):
        # Get today's date
        today = datetime.today()
        # Calculate the difference in years
        age = today.year - dob.year
        # Adjust the age if the birthday hasn't occurred yet this year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age

    @hybrid_property
    def age(self):
        if self.dob:
            return User.calculate_age(self.dob)

    @hybrid_property
    def work_tenure(self):
        if self.start_date:
            return User.calculate_tenure(self.start_date)

    @hybrid_property
    def full_name(self):
        if self.first_name and self.middle_name and self.last_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"


    @hybrid_property
    def avatar(self):
        """
        two paths - one is a root path for checking image exists
        other deform_path returns for use with macro avatar url_for
        """
        # if no image exists use default image
        if not self.image_file:
            return os.path.join('/static/img', 'default.png')
        # otherwise return saved image_file
        url = url_for('user.get_uploaded_profile_img', filename=self.image_file)
        return url

    @hybrid_property
    def leave_year_start_fmt(self):
        if self.leave_year_start:
            return self.leave_year_start.strftime("%-d %b %Y")
        return self.leave_year_start


    @hybrid_property
    def active_departments(self):
        from app.department.models import Department, DepartmentMembers
        depts = db.session.query(Department).join(DepartmentMembers) \
                           .filter(Department.active,
                                   DepartmentMembers.user_id==self.id) \
                           .all()
        return depts


    def all_departments_events(self):
        from app.department.models import Department, DepartmentMembers
        events = db.session.query(Event) \
                .join(User) \
                .join(Department, User.department) \
                .filter(Department.active,
                        DepartmentMembers.user_id==self.id,
                        Event.status!='Declined',
                        Event.status!='Revoked')
        return events.all()

    @classmethod
    def find_by_identity(cls, identity):
        """
        Find a user by their email or username
        """
        return User.query.filter(
            # TODO ldap filter string needs to be both username or email
            #(User.email == identity.lower()) | (User.username == identity.lower())).first()
            # therefore login with only username for now
           User.username == identity.lower()).first()

    @classmethod
    def initialize_password_reset(cls, email):
        u = User.find_by_email(email)
        reset_token = u.serialize_token()

    def serialize_token(self, expiration=1800):
        """ Sign and create a token that can be used with a one off token such
        as resetting password etc. Token default expiry is 1800 secs / 30 mins."""
        return jwt.encode(
                {'reset_password': self.id, 'exp': time() + expiration},
                str(os.environ.get('SECRET_KEY')), algorithm='HS256')

    @staticmethod
    def verify_password_reset_token(token):
        try:
            id = jwt.decode(token, str(os.environ.get('SECRET_KEY')),
                            algorithms=['HS256'])['reset_password']
        except Exception as e:
            print(e)
            return
        return User.query.get(id)

    def authenticated(self, with_password=True, password=''):
        """
        Ensure a user is authenticated, and optionally check their password.
        :param with_password: Optionally check their password
        :type with_password: bool
        :param password: Optionally verify this as their password
        :type password: str
        :return: bool
        """
        if with_password:
            return check_password_hash(self.password, password)
        return True

    @classmethod
    def encrypt_password(cls, plaintext_password):
        if plaintext_password:
            return generate_password_hash(plaintext_password)
        return None

    @classmethod
    def is_last_admin(cls, user):
        """
        Determine whether or not this user is the last admin account.

        :param user: User being tested
        :type user: User
        :param new_role: New role being set
        :type new_role: str
        :param new_active: New active status being set
        :type new_active: bool
        :return: bool
        """
        if user.role:
            if user.role.superuser:
                admin_count = User.query.join(Role) \
                                .filter(Role.superuser == True 
                                        and User.active == True) \
                                .count()
                if admin_count == 1:
                    return True
        return False

    @classmethod
    def bulk_send_welcome_email(cls, ids):
        welcome_email = 0

        for id in ids:
            user = User.query.get(id)
            if user is None:
                continue
            from app.email import send_activation_email
            send_activation_email(user)
            welcome_email += 1
        return welcome_email

    @classmethod
    def bulk_password_reset(cls, ids):
        reset_count = 0

        for id in ids:
            user = User.query.get(id)
            if user is None:
                continue
            from app.email import send_password_reset_email
            send_password_reset_email(user)
            reset_count += 1
        return reset_count

    def update_login_activity(self, ip_address):
        """
        Update account metadata
        such as current and previous login times
        as well as ip addresses etc.
        """
        self.previous_login_time = self.current_login_time
        self.current_login_time = datetime.utcnow()

        self.previous_login_ip_address = self.current_login_ip_address
        self.current_login_ip_address = ip_address

        return self.save()

    def deduct_leave_days(self, days):
        self.used_days = self.used_days + days
        self.days_left = self.days_left - days

    def reinstate_allowance_days(self, days):
        self.used_days -= days
        self.days_left += days

    def is_active(self):
        return self.active


    def paginated_events(self, page):
        sort_by = Event.sort_by(request.args.get('sort', 'start_date'),
                               request.args.get('direction', 'desc'))
        order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
        events = Event.query \
                .filter(Event.user_id==self.id) \
                .order_by(text(order_values)) \
                .paginate(page, get_settings_value('events_per_page'), False)
        return events

    def pending_or_approved_events(self):
        events = Event.query \
                .filter(Event.user==self,
                        Event.status!='Declined',
                        Event.status!='Revoked') \
                .all()
        return events

    def is_authoriser(self):
        """ check if user is an authoriser to anyone else """
        if User.query.filter(User.authoriser==self).first():
            return True
        return False

    def count_authoriser_requests(self):
        events = db.session.query(Event).join(User) \
                .filter(User.authoriser==self) \
                .count()
        return events

    def pending_authoriser_requests(self):
        events = db.session.query(Event).join(User) \
                .filter(User.authoriser==self, Event.status=='Pending')
        return events

    def paginated_pending_authoriser_requests(self, page):
        events = self.pending_authoriser_requests() \
                .paginate(page, get_settings_value('events_per_page'), False)
        return events

    def paginated_actioned_authoriser_requests(self, page):
        events = db.session.query(Event).join(User) \
                .filter(User.authoriser==self, Event.status!='Pending') \
                .paginate(page, get_settings_value('events_per_page'), False)
        return events

    @classmethod
    def calculate_leave_days(cls):
        return User._group_and_count(User, User.role)

    @classmethod
    def _group_and_count(cls, model, field):
        count = func.count(field)
        query = db.session.query(count, field).group_by(field).all()

        results = {
                'query': query,
                'total': model.query.count()
                }
        return results

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (User.email.ilike(search_query),
                        User.username.ilike(search_query))

        return or_(*search_chain)

    def serialize(self):
        return {
                'id': f'@{self.username}',
                'userId': self.id,
                'name': self.username,
                'link': url_for('user.profile', id=self.id)
                }

    def add_notification(self, data, endpoint):
        #self.notifications.filter_by(name=name).delete()
        n = Notification(payload_json=json.dumps(data), endpoint=endpoint, user=self)
        n.save()

    def new_notifications(self):
        last_read_time = self.last_notification_read_time or datetime(1900, 1, 1)
        return Notification.query.filter_by(user_id=self.id).filter(
            Notification.created_at > last_read_time).count()

    def delete_all_notifications(self):
        Notification.query.filter(Notification.user_id==self.id).delete()
        return db.session.commit()

    @classmethod
    def bulk_delete_notifications(cls, ids):
        delete_count = 0

        for id in ids:
            n = Notification.query.get(id)
            if n is None:
                continue
            else:
                n.delete()
                delete_count += 1
        return delete_count

    def display_leave_allowance(self):
        columns = [
            [self.annual_entitlement, 'Annual Entitlement'],
            [self.carry_over_days, 'Days Carried Over From Last Year'],
            [self.used_days,'Used and Authorised Days'],
            [self.days_left, 'Days Left']
        ]
        for column in columns:
            if column[0].as_integer_ratio()[1] == 1:
                column[0] = int(column[0])
                yield column
            else:
                yield column

    def is_last_superuser(self):
        if self.role:
            if self.role.superuser:
                user_count = db.session.query(User).join(Role) \
                        .filter(Role.superuser).count()
                if user_count == 1:
                    return True



class Notification(ResourceMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    payload_json = db.Column(db.Text)
    endpoint = db.Column(db.String(200))

    def get_data(self):
        return json.loads(str(self.payload_json))

    def __repr__(self):
        return self.payload_json
