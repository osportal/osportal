from app.admin.models import Settings, Email
from app.department.models import Department, DepartmentMembers
from app.extensions import db
from app.event.models import Event
from app.models import Country, PublicHoliday
from app.posts.forms import PostForm
from app.user.forms import UserForm
from app.user.models import User, Role, Permission
from app.user.validations import check_username_exists, check_email_exists, check_authoriser
from app.utils.util_wtforms import ModelForm, choices_from_dict
from app.utils.csv import dump_database_table
from collections import OrderedDict
from flask import request
from flask_admin.form.widgets import Select2Widget
from flask_wtf import FlaskForm
#from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from sqlalchemy import func
from wtforms import (StringField, PasswordField, IntegerField,
                     DecimalField,
                     SubmitField, BooleanField, TextAreaField,
                     SelectField, SelectMultipleField, HiddenField, DateField,
                     EmailField, FileField)
from wtforms_alchemy import Unique
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.widgets import ColorInput
from wtforms.fields import DateField as DatePickerField
from wtforms.validators import (DataRequired, Regexp, ValidationError,
                                Length, EqualTo, NumberRange,
                                Optional)
# import email validator as different name due to naming conflict with admin model Email
from wtforms.validators import Email as EmailVal
from wtforms.widgets import HiddenInput, PasswordInput


class LDAPForm(ModelForm):
    ldap_bind_username = StringField('LDAP Username', validators=[DataRequired(), Length(1,128)])
    ldap_bind_password = PasswordField('LDAP Password', widget=PasswordInput(hide_value=False), validators=[DataRequired()])
    ldap_host = StringField('LDAP Server', validators=[DataRequired(), Length(1,500)])
    ldap_port = IntegerField('LDAP Server Port', validators=[Optional()])
    active_directory = BooleanField('Active Directory', validators=[Optional()])
    domain_name = StringField('Domain Name', validators=[Optional(), Length(1, 64)])

    ldap_search = StringField('LDAP Search / Root DN', validators=[DataRequired(), Length(1,500)])
    ldap_uid_field = StringField('LDAP UID Field', validators=[DataRequired(), Length(1,500)])
    ldap_user_registration = BooleanField('LDAP User Registration', validators=[Optional()])
    ldap_firstname_field = StringField('LDAP First Name Field', validators=[DataRequired(), Length(1,500)])
    ldap_lastname_field = StringField('LDAP Last Name Field', validators=[DataRequired(), Length(1,500)])
    ldap_email_field = StringField('LDAP User Email Field', validators=[DataRequired(), Length(1,500)])


class AdminPostForm(PostForm):
    locked = BooleanField()
    is_pin = BooleanField('Pin Post')
    user = QuerySelectField('Author',
                            query_factory=lambda: User.query.filter(User.active).all(),
                            widget=Select2Widget(),
                            allow_blank=False,
                            validators=[DataRequired()]
                            )


class CountryForm(ModelForm):
    code = StringField('Alpha Code', validators=[DataRequired(), Length(1, 5)])
    name = StringField(validators=[DataRequired(), Length(1, 100)])
    # TODO days need DataRequired validator instead of Optional
    default_annual_allowance = IntegerField('Default Annual Entitlement', validators=[Optional(), NumberRange(min=0,max=100)])
    default_carry_over_days = IntegerField('Default Carry Over Days', validators=[Optional(), NumberRange(min=0, max=100)])


class PublicHolidayYearForm(ModelForm):
    year = SelectField("Filter by Year", choices=[], render_kw={'id': 'year_filter'})


class PublicHolidayForm(ModelForm):
    name = StringField(validators=[DataRequired(), Length(1, 200)])
    active = BooleanField('Active')
    start_date = DatePickerField('Date', validators=[DataRequired()])


class PageForm(FlaskForm):
    custom_message = 'Only alphanumeric characters and hyphens are supported.'
    name = StringField(validators=[
        DataRequired(),
        Length(1, 25),
        # Part of the Python 3.7.x update included updating flake8 which means
        # we need to explicitly define our regex pattern with r'xxx'.
    ])
    active = BooleanField('Active')
    route = StringField(validators=[DataRequired(),
                                    Length(1,128),
                                    Regexp(r'^[\w-]+$', message=custom_message)
                                    ])
    content = TextAreaField('Content', validators=[DataRequired()], render_kw={'id': 'ckeditor'})


class NewUserForm(UserForm):

    role = QuerySelectField('Role', query_factory=lambda: Role.query.all(), get_pk=lambda r: r.id, allow_blank=True,
                            validators=[Optional()])
    active = BooleanField('Allow this user to sign in')
    send_activation_account_email = BooleanField('Send activation account email')
    department = QuerySelectMultipleField('Departments', query_factory=lambda: Department.query.all(),
                                          widget=Select2Widget(), allow_blank=True,
                                          render_kw={"multiple": "multiple"}, validators=[Optional()])
    authoriser = QuerySelectField('Leave Authoriser', query_factory=lambda: User.query.all(), widget=Select2Widget(),
                                  allow_blank=True, validators=[Optional(), check_authoriser])
    job_title = StringField(validators=[Optional(), Length(1, 50)])
    leave_year_start = DateField('Leave Year Start', validators=[Optional()])
    annual_entitlement = DecimalField('Annual Entitlement', validators=[Optional(), NumberRange(min=0, max=100)],places=1)
    total_holiday_entitlement = DecimalField('Total Holiday Entitlement', validators=[Optional(), NumberRange(min=0, max=100)],places=1)
    carry_over_days = DecimalField('Carry Over Days', validators=[Optional(), NumberRange(min=0, max=100)],places=1)
    used_days = DecimalField('Used Days', validators=[Optional(), NumberRange(min=0, max=100)],places=1)
    days_left = DecimalField('Days Left', validators=[Optional(), NumberRange(min=0, max=100)],places=1)
    #country = QuerySelectField('Country', query_factory=lambda: Country.query.order_by(Country.name).all(),
    #                           widget=Select2Widget(), allow_blank=False, validators=[DataRequired()],
    #                           default=lambda: Country.query.filter(Country.name=='United Kingdom').first())


class NewDepartmentForm(ModelForm):
    name = StringField(validators=[
        Unique(Department.name),
        DataRequired(),
        Length(1, 65),
    ])
    description = StringField(validators=[Optional(), Length(0, 350)])
    members = QuerySelectMultipleField('Members', query_factory=lambda: User.query.all(),
                                       get_pk=lambda u: u.id, widget=Select2Widget(), allow_blank=True,
                                       render_kw={"multiple": "multiple"}, validators=[DataRequired()])


class EditDepartmentForm(NewDepartmentForm):
    head = QuerySelectField('Head',
                            query_factory=lambda: User.query.filter(DepartmentMembers.user_id==User.id) \
                                    .filter(DepartmentMembers.department_id==request.view_args['id']).all(),
                            widget=Select2Widget(), allow_blank=True, validators=[Optional()])


class RoleForm(ModelForm):
    #custom_message = 'Alphanumeric characters only please.'

    name = StringField(validators=[DataRequired(),
                                   Length(1, 30),
                                   #Regexp(r'^[\w &]+$', message=custom_message)
                                   ])
    description = StringField(validators=[Optional(), Length(0, 120)])
    permissions = QuerySelectMultipleField('Permissions',
                                           query_factory=lambda: Permission.query.all(),
                                           widget=Select2Widget(),
                                           allow_blank=True,
                                           render_kw={"multiple": "multiple"},
                                           validators=[Optional()]
                                           )
    superuser = BooleanField('Superuser?')
    # UserAdmin
    user_admin_view = BooleanField('Read - Ability to access the User Admin Page')
    user_admin_add = BooleanField('Create - Ability to add new users')
    user_admin_edit = BooleanField('Edit - Ability to edit existing user information')
    user_admin_delete = BooleanField('Delete - Ability to delete users')

    ## Department admin
    dept_admin_view = BooleanField('Read - Ability to access the Department Admin Page')
    dept_admin_add = BooleanField('Create - Ability to add new departments')
    dept_admin_edit = BooleanField('Edit - Ability to edit existing department information')
    dept_admin_delete = BooleanField('Delete - Ability to delete departments')

    ## System admin
    #sys_admin_view = db.Column(db.Boolean, default=False)
    #sys_admin_add = db.Column(db.Boolean, default=False)
    #sys_admin_edit = db.Column(db.Boolean, default=False)
    #sys_admin_delete = db.Column(db.Boolean, default=False)

    create_posts = BooleanField('Can Create Posts?')
    edit_any_post = BooleanField('Edit Any Post?')
    delete_any_post = BooleanField('Delete Any Post?')
    pin_posts = BooleanField('Can Pin Posts?')
    create_comments = BooleanField('Can Create Comments?')
    edit_any_comment = BooleanField('Edit Any Comment?')
    delete_any_comment = BooleanField('Delete Any Comment?')


exclusions = ['event_actioned', 'role_permission', 'notification', 'department_members']
class PermissionForm(ModelForm):
    choices = ['admin.' + str(k) for k in db.metadata.tables.keys() if k not in exclusions]
    choices += [k for k in  db.metadata.tables.keys() if k=='comment' or k=='post']

    #custom_message = 'Alphanumeric characters only please.'
    name = StringField(validators=[DataRequired(),
                                   Length(1, 30),
                                   #Regexp(r'^[\w &]+$', message=custom_message)
                                   ])
    description = StringField(validators=[Optional(), Length(0, 350)])
    db_name = SelectField("Object Type", choices=choices)
    create = BooleanField('Create')
    read = BooleanField('Read')
    update = BooleanField('Update')
    delete = BooleanField('Delete')


class EventTypeSettingsForm(ModelForm):
    name = StringField('Name', validators=[DataRequired()])
    active = BooleanField('Active')
    #hex_colour = StringField('Colour', validators=[DataRequired()])
    hex_colour = StringField('Colour', widget=ColorInput())
    deductable = BooleanField('Deduct days from allowance?')
    approval = BooleanField('Approval required?')
    max_days = IntegerField('Maximum Length (days)', validators=[DataRequired()])


class EventRequestsForm(ModelForm):
    #status = SelectField('Status', choices=[Event.STATUS], validators=[DataRequired()])
    status = SelectField('Status', validators=[DataRequired()], choices=Event.STATUS)


class SearchForm(FlaskForm):
    q = StringField('Search terms', [Optional(), Length(1, 256)])


class SettingsForm(FlaskForm):
    site_name = StringField('Intranet Name/Title', validators=[DataRequired(), Length(2, 25)])
    company_name = StringField('Company Name', validators=[Optional(), Length(2, 30)])
    company_website = StringField('Company Website', validators=[Optional(), Length(3, 40)])

    # Auth
    auth_type = SelectField(choices=['DB'], validators=[DataRequired()])
    user_registration = BooleanField('Enable User Registration', validators=[Optional()])
    reg_user_role = QuerySelectField('User Registration Role',
                                     query_factory=lambda: Role.query.all(),
                                     widget=Select2Widget(), allow_blank=True,
                                     validators=[Optional()]
                                     )
    reg_user_country = QuerySelectField('User Registration Country',
                                        query_factory=lambda: Country.query.order_by(Country.name.asc()).all(),
                                        widget=Select2Widget(), allow_blank=True,
                                        validators=[Optional()]
                                        )
    # Pagination
    items_per_admin_page = IntegerField('Max. items per admin page', validators=[DataRequired(), NumberRange(5, 250)])
    users_per_page = IntegerField('Max. users per page', validators=[DataRequired(), NumberRange(5, 250)])
    departments_per_page = IntegerField('Max. departments per page', validators=[DataRequired(), NumberRange(5, 250)])
    posts_per_page = IntegerField('Max. posts per page', validators=[DataRequired(), NumberRange(5, 250)])
    comments_per_page = IntegerField('Max. comments per page', validators=[DataRequired(), NumberRange(5, 250)])
    events_per_page = IntegerField('Max. events per page', validators=[DataRequired(), NumberRange(5, 250)])
    notifications_per_page = IntegerField('Max. notifications per page', validators=[DataRequired(), NumberRange(5, 250)])

    #Email
    system_email = QuerySelectField('System Email',
                                    query_factory=lambda: Email.query.all(),
                                    get_pk=lambda s: s.id,
                                    allow_blank=True,
                                    validators=[Optional()]
                                    )
    alert_email = QuerySelectField('Alert Email',
                                   query_factory=lambda: Email.query.all(),
                                   get_pk=lambda s: s.id,
                                   allow_blank=True,
                                   validators=[Optional()]
                                   )

    #Calendar
    weekend =BooleanField('Enable Weekends')
    half_day = BooleanField('Enable Half Days')
    pending_colour = StringField('Pending Colour', widget=ColorInput())
    declined_colour = StringField('Declined Colour', widget=ColorInput())
    public_holiday_colour = StringField('Public Holiday Colour', widget=ColorInput())


class EmailForm(FlaskForm):
    name = StringField('Display Name', validators=[DataRequired(), Length(1, 50)])
    email = EmailField('Send Email From', validators=[DataRequired()])
    server = StringField('Mail Server', validators=[DataRequired()])
    port = IntegerField('Mail Port', validators=[DataRequired()])
    username = StringField('Mail Username')
    password = PasswordField('Mail Password', widget=PasswordInput(hide_value=False))
    ssl = BooleanField('SSL/TLS')
    starttls = BooleanField('STARTTLS')
    auth = BooleanField('Use Mail Server Username and Password?')


class UpdateAccountForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), EmailVal()])
    email_nots = BooleanField('Receive email notifications')
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That username is taken. Please use another')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please use another')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
                             validators=[DataRequired(),
                                         Length(min=8)])
    password2 = PasswordField('Confirm Password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                          message='Passwords must match')])
    show_password = BooleanField('Show Password', id='check')
    submit = SubmitField('Change Password')


class ImportZipForm(FlaskForm):
    zip_file = FileField("Zip File", description="Zip file contents")
    submit = SubmitField("Import Zip")


class ImportCSVForm(FlaskForm):
    csv_type = SelectField("Database Table", choices=lambda: db.metadata.tables.keys())
    csv_file = FileField("CSV File", description="CSV file contents")
    submit = SubmitField("Import CSV")


class ExportCSVForm(FlaskForm):
    table_name = SelectField("Database Table", choices=lambda: db.metadata.tables.keys())
    submit = SubmitField("Download CSV")
