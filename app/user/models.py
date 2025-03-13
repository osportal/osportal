from app.admin.utils import get_settings_value
from app.extensions import db
from app.models import get_class_by_tablename, Site
from app.leave.models import Leave
from app.posts.models import Comment
from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from flask_continuum import VersioningMixin
from flask_login import UserMixin, logout_user, current_user
from flask import url_for, current_app, request
import json
import jwt
import os
from sqlalchemy import text, or_, func, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
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

    # Post Permissions
    # TODO change nullable=False
    can_create_posts = db.Column(db.Boolean, nullable=True, default=True)
    can_edit_posts = db.Column(db.Boolean, nullable=True, default=True)
    can_delete_posts = db.Column(db.Boolean, nullable=True, default=True)
    # Comment Permissions
    can_create_comments = db.Column(db.Boolean, nullable=True, default=True)
    can_edit_comments = db.Column(db.Boolean, nullable=True, default=True)
    can_delete_comments = db.Column(db.Boolean, nullable=True, default=True)

    # Profile permissions
    user_edit_email = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_username = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_first_name = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_middle_name = db.Column(db.Boolean, nullable=True, default=False)
    user_edit_last_name = db.Column(db.Boolean, nullable=True, default=False)
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



class User(UserMixin, ResourceMixin, VersioningMixin):
    __tablename__ = 'user'
    __versioning__ = {
        'exclude': ['password', 'updated_at']  # Exclude this field from versioning
    }
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
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
    entt_id = db.Column(db.Integer, db.ForeignKey('entt.id'), nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=True)

    last_notification_read_time = db.Column(db.DateTime)

    # Work
    job_title = db.Column(StripStr(100))
    authoriser_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    start_date = db.Column(db.Date, nullable=True)

    # Login Info
    login_time = db.Column(db.DateTime, default=datetime.utcnow())
    login_ip_address = db.Column(db.String(50))

    # Leave Days
    leave_year_start = db.Column(db.Date, default=datetime.now().date().replace(month=1, day=1))

    entitlement_used = db.Column(db.Numeric(precision=6, scale=2), default=0)
    entitlement_rem = db.Column(db.Numeric(precision=6, scale=2), default=0)
    previous_carryover = db.Column(db.Numeric(precision=6, scale=2), default=0)

    # RELATIONSHIPS
    role = db.relationship("Role", foreign_keys=[role_id], backref='user')
    entt = db.relationship("Entt", foreign_keys=[entt_id], backref='user')
    authoriser = db.relationship(lambda: User,
                                 remote_side=id,
                                 backref=db.backref('lauthoriser', lazy='dynamic')
                                 )
     # Explicitly specify the foreign key for the relationship with 'Leave'
    leaves = db.relationship('Leave',
                             backref=db.backref('user', lazy='select'),
                             foreign_keys=[Leave.user_id],  # Specify which foreign key to use
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
    site = db.relationship('Site', foreign_keys=[site_id], backref='user')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = User.encrypt_password(kwargs.get('password', ''))
        #self.annual_entitlement = self.country.default_annual_allowance
        #self.days_left = self.annual_entitlement

    # Ensure the password is not used in version history by overriding the method for getting the version
    @declared_attr
    def __versioned__(cls):
        return {
            'exclude': ['password', 'updated_at'],  # Make sure password isn't included in version history
        }

    def __repr__(self):
        return self.display_name

    def __str__(self):
        return self.display_name


    def can_permission(self, permission):
        if self.role:
            access = self.role.check_permissions(permission)
            return access

    # admin permission
    def permission(self, *obj, crud):
        if self.role:
            access = self.role.check_admin_access(obj, crud)
            return access

    def post_permissions(self, action, post=None):
        """
        Check if the user has permission for a given action on a post.
        """
        if self.role:
            if action == 'edit':
                return (post and post.user == self and self.can_permission('can_edit_posts'))
            elif action == 'delete':
                return (post and post.user == self and self.can_permission('can_delete_posts'))
            return False
        return False

    def comment_permissions(self, action, comment=None):
        """
        Check if the user has permission for a given action on a comment.
        """
        if self.role:
            if action == 'edit':
                return (comment and comment.user == self and self.can_permission('can_edit_comments'))
            elif action == 'delete':
                return (comment and comment.user == self and self.can_permission('can_delete_comments'))
            elif action == 'create':
                return (comment and comment.user != self and self.can_permission('can_create_comments'))
            return False
        return False


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
    def display_name(self):
        return f"{self.first_name} {self.last_name}"

    @hybrid_property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        return func.concat(
            cls.first_name,
            " ",
            func.coalesce(cls.middle_name + " ", ""),
            cls.last_name
        )


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

    def get_annual_leave_days(self):
        if self.entt:
            return self.entt.default_entitlement
        return 0

    def get_entt_weekend(self):
        if self.entt:
            return self.entt.weekend
        else:
            return False

    def get_entt_id(self):
        if self.entt:
            return self.entt.id
        return 0

    def init_entt(self):
        if self.entt:
            self.entitlement_rem = self.entt.default_entitlement
            self.entitlement_used = 0 # Reset used entitlement for the chosen template
            self.previous_carryover = 0 # Reset previous carry over days for the chosen template
            return self.save()

    def get_leave_types(self):
        if self.entt:
            return self.entt.leave_types
        return []

    def check_public_holidays(self):
        ##TODO redo this horrible shit
        if self.entt:
            if self.entt.public_holiday_group:
                return self.entt.public_holiday_group.holidays
        return []


    @hybrid_property
    def active_departments(self):
        from app.department.models import Department, DepartmentMembers
        depts = db.session.query(Department).join(DepartmentMembers) \
                           .filter(DepartmentMembers.user_id==self.id) \
                           .all()
        return depts


    def all_departments_leaves(self):
        from app.department.models import Department, DepartmentMembers
        leaves = db.session.query(Leave) \
                .join(User) \
                .join(Department, User.department) \
                .filter(DepartmentMembers.user_id==self.id,
                        Leave.status!='Declined',
                        Leave.status!='Revoked')
        return leaves.all()

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
        Update metadata for login times and ip addresses etc.
        """
        self.login_time = datetime.utcnow()
        self.login_ip_address = ip_address

        return self.save()

    def deduct_leave_days(self, days):
        self.entitlement_used += Decimal(days)
        self.entitlement_rem -= Decimal(days)

    def reinstate_allowance_days(self, days):
        self.entitlement_used -= Decimal(days)
        self.entitlement_rem += Decimal(days)

    def carryover_entitlement(self):
        if not self.entitlement_rem:
            raise Exception('Entitlement Remaining is null')
        if not self.entt:
            raise Exception('User has no Entitlement Template')
        # Maximum carryover allowed
        max_carryover = min(self.entitlement_rem, self.entt.max_carryover)

        # Calculate the potential new entitlement
        potential_entitlement = self.entt.default_entitlement + max_carryover
        entitlement_cap = self.entt.entitlement_cap  # Assume this attribute defines the cap

        # Adjust carryover to reach the cap if there's room
        if potential_entitlement > entitlement_cap:
            # Reduce carryover to not exceed the entitlement cap
            max_carryover = entitlement_cap - self.entt.default_entitlement

        # Calculate the final entitlement within the cap
        new_entitlement = self.entt.default_entitlement + max_carryover

        # Update user attributes
        self.previous_carryover = max_carryover
        self.entitlement_rem = new_entitlement
        self.entitlement_used = 0  # Reset used entitlement for the new period

        # Save changes to the database
        self.save()

    def is_active(self):
        return self.active


    def paginated_leaves(self, page):
        sort_by = Leave.sort_by(request.args.get('sort', 'start_date'),
                               request.args.get('direction', 'desc'))
        order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
        leaves = Leave.query \
                .filter(Leave.user_id==self.id) \
                .order_by(text(order_values)) \
                .paginate(page, 15, False)
        return leaves

    def pending_or_approved_leaves(self):
        leaves = Leave.query \
                .filter(Leave.user==self,
                        Leave.status!='Declined',
                        Leave.status!='Revoked') \
                .all()
        return leaves

    def is_authoriser(self):
        """ check if user is an authoriser to anyone else """
        if User.query.filter(User.authoriser==self).first():
            return True
        return False

    def pending_authoriser_requests(self):
        leaves = db.session.query(Leave).join(User) \
                .filter(User.authoriser==self, Leave.status=='Pending') \
                .order_by(Leave.created_at.desc())
        return leaves

    def paginated_pending_authoriser_requests(self, page):
        leaves = self.pending_authoriser_requests() \
                .paginate(page, 15, False)
        return leaves

    def paginated_actioned_authoriser_requests(self, page):
        leaves = db.session.query(Leave).join(User) \
                .filter(User.authoriser==self, Leave.status!='Pending') \
                .order_by(Leave.start_date.desc()) \
                .paginate(page, 15, False)
        return leaves

    def paginated_authoriser_users(self, page):
        users = User.query \
                .filter(User.authoriser==self) \
                .filter(User.search((request.args.get('q', text(''))))) \
                .order_by(User.full_name.asc()) \
                .paginate(page, 15, False)
        return users

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
        search_query = f'%{query}%'
        # Construct dynamic full_name conditions
        with_middle_name = func.concat(cls.first_name, ' ', cls.middle_name, ' ', cls.last_name).ilike(search_query)
        without_middle_name = func.concat(cls.first_name, ' ', cls.last_name).ilike(search_query)

        search_chain = [cls.email.ilike(search_query),
                        cls.username.ilike(search_query),
                        cls.job_title.ilike(search_query),
                        with_middle_name,  # Match full name with middle name
                        without_middle_name  # Match full name without middle name
                        ]

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
        if self.entt:
            unit = self.entt.time_unit.title()
            columns = [
                [self.get_annual_leave_days(), 'Annual Entitlement'],
                [self.previous_carryover, f'{unit} Carried Over'],
                [self.entitlement_rem, f'{unit} Remaining'],
                [self.entitlement_used, f'Used and Authorised {unit}'],
            ]
            for column in columns:
                if column[0] is not None:
                    if column[0].as_integer_ratio()[1] == 1:
                        column[0] = int(column[0])  # Convert to int if it's a whole number
                    else:
                        column[0] = float(column[0])  # Ensure it's a float
                        # Format the float to strip unnecessary zeros
                        column[0] = float(f"{column[0]:g}")
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
