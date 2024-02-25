from celery import __version__ as celery_version
import csv
from flask import (url_for, redirect, abort, request, flash, Blueprint, render_template,
                   send_file, jsonify, current_app)
from flask import __version__ as flask_version
from flask_login import current_user, login_required
from io import BytesIO, StringIO
from sqlalchemy import text
from sqlalchemy.exc import PendingRollbackError, IntegrityError
from psycopg2.errors import UniqueViolation

from app.admin.decorators import admin_read_required
from app.admin.forms import (SearchForm, NewUserForm, RoleForm, PermissionForm,
                             EditDepartmentForm, NewDepartmentForm,
                             SettingsForm, PageForm, EventTypeSettingsForm,
                             EventRequestsForm, ImportCSVForm, ExportCSVForm,
                             ImportZipForm, PublicHolidayForm, CountryForm,
                             SystemEmailForm, ResetPasswordForm, PublicHolidayYearForm,
                             LDAPForm)
from app.admin.models import Dashboard, Settings, SystemEmail
from app.admin.utils import get_settings_value
from app.department.models import Department, DepartmentMembers
from app.extensions import db
from app.models import Country, PublicHoliday, get_class_by_tablename
from app.event.models import Event, EventType
from app.pages.models import Page
#from app.user.auth import ldap_con
from app.user.decorators import permission_required
from app.user.models import User, Role, Permission
from app.user.forms import RegistrationForm
from app.utils.csv import load_csv, dump_csv, dump_table_selected_ids
from app.utils.zip import export_zipfile, import_zipfile


admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.before_request
@login_required
def before_request():
    """ Protect all admin endpoints """
    pass


# INDEX PAGES

@admin.route('/')
@admin_read_required()
def dashboard():
    stats = {
        "celery_version": celery_version,
        "flask_version": flask_version,
        "group_and_count_pages": Dashboard.group_and_count_pages(),
        "group_and_count_users": Dashboard.group_and_count_users(),
        "group_and_count_roles": Dashboard.group_and_count_roles(),
        "group_and_count_permissions": Dashboard.group_and_count_permissions(),
        "group_and_count_departments": Dashboard.group_and_count_departments(),
        "group_and_count_event_types": Dashboard.group_and_count_event_types(),
        "group_and_count_emails": Dashboard.group_and_count_emails(),
        "group_and_count_countries": Dashboard.group_and_count_countries()
    }
    return render_template('admin_dashboard.html', **stats)


@admin.route('/emails', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/emails/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.system_email', crud='read')
def emails(page):
    search_form = SearchForm()
    sort_by = SystemEmail.sort_by(request.args.get('sort', 'name'),
                              request.args.get('direction', 'asc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
    paginated_emails = SystemEmail.query \
        .filter(SystemEmail.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)
    return render_template('email/index.html',
                           form=search_form,
                           emails=paginated_emails)


@admin.route('/countries', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/countries/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.country', crud='read')
def countries(page):
    search_form = SearchForm()
    sort_by = Country.sort_by(request.args.get('sort', 'name'),
                              request.args.get('direction', 'asc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
    paginated_countries = Country.query \
        .filter(Country.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)
    return render_template('country/index.html',
                           form=search_form,
                           countries=paginated_countries)


@admin.route('/countries/<int:id>', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/countries/<int:id>/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.country', crud='read')
@permission_required('admin.public_holiday', crud='read')
def country(id, page):
    country = Country.query.get_or_404(id)
    list_years = PublicHoliday.unique_years_by_country(country.id)
    paginated_holidays = None
    form = PublicHolidayYearForm()
    dropdown_year = request.args.get('year')
    if list_years:
        if not dropdown_year:
            dropdown_year = list_years[0]
        form.year.choices = list_years
        paginated_holidays = PublicHoliday.query \
                .filter(PublicHoliday.country_id==country.id,
                        PublicHoliday.filter_year(dropdown_year)) \
                .paginate(page, get_settings_value('items_per_admin_page'), True)
    return render_template('country/country.html',
                           form=form,
                           country=country,
                           years=list_years,
                           dropdown_year=dropdown_year,
                           paginated_holidays=paginated_holidays,
                           )


@admin.route('/departments', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/departments/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.department', crud='read')
def departments(page):
    search_form = SearchForm()

    sort_by = Department.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_departments = Department.query \
        .filter(Department.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('department/index.html',
                           form=search_form,
                           departments=paginated_departments)


@admin.route('/events', defaults={'page':1}, methods=['GET', 'POST'])
@admin.route('/events/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.event', crud='read')
def events(page):
    search_form = SearchForm()

    sort_by = EventType.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_etypes = EventType.query \
        .filter(EventType.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('event/index.html', event_types=paginated_etypes)


@admin.route('/events/requests', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/events/requests/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.event', crud='read')
def event_requests(page):
    events = Event.query \
            .paginate(page, get_settings_value('items_per_admin_page'), False)
    return render_template('event/requests_index.html', events=events)


@admin.route('/users', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/users/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='read')
def users(page):
    search_form = SearchForm()
    #import_form = ImportCSVForm()
    #import_form.csv_type.data = 'user'

    sort_by = User.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_users = User.query \
        .filter(User.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('user/index.html',
                           #form=import_form,
                           form=search_form,
                           users=paginated_users)


@admin.route('/roles', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/roles/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.role', crud='read')
def roles(page):
    search_form = SearchForm()
    sort_by = Role.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_roles = Role.query \
        .filter(Role.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('role/index.html',
                           form=search_form,
                           roles=paginated_roles)


@admin.route('/permissions', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/permissions/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.permission', crud='read')
def permissions(page):
    search_form = SearchForm()
    sort_by = Permission.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    #first order value is in double quotes because 'create' is keyword in postgres
    # and throws syntax error
    order_values = '"{0}" {1}'.format(sort_by[0], sort_by[1])

    paginated_permissions = Permission.query \
        .filter(Permission.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('permission/index.html',
                           form=search_form,
                           permissions=paginated_permissions)


@admin.route('/pages', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/pages/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.page', crud='read')
def pages(page):
    search_form = SearchForm()
    pages = Page.query \
            .paginate(page, get_settings_value('items_per_admin_page'), False)
    return render_template('pages/index.html', pages=pages, form=search_form)


@admin.route('/pages/new', methods=['GET', 'POST'])
@permission_required('admin.page', crud='create')
def pages_new():
    page = Page()
    form = PageForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(page)
            page.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created.', 'success')
            return redirect(url_for('admin.pages'))
    else:
        for error in form.errors.items():
            print(error)
    return render_template('pages/edit.html', form=form)


@admin.route('/pages/edit/<int:id>', methods=['GET', 'POST'])
def pages_edit(id):
    page = Page.query.get(id)
    form = PageForm(obj=page)
    if form.validate_on_submit():
        try:
            form.populate_obj(page)
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            page.save()
            flash('Updated successfully.', 'success')
            return redirect(url_for('admin.pages'))
    return render_template('pages/edit.html', form=form, page=page)


@admin.route('/pages/<int:id>/delete', methods=['POST'])
@permission_required('admin.page', crud='delete')
def pages_delete(id):
    page = Page.query.get_or_404(id)
    try:
        page.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {page.name}', 'success')
    return redirect(url_for('admin.pages'))


@admin.route('/settings/edit', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='update')
def settings_edit():
    settings = Settings.query.first_or_404()
    form = SettingsForm(obj=settings)
    if form.validate_on_submit():
        form.populate_obj(settings)
        settings.save()
        flash('Settings saved successfully.', 'success')
    return render_template('settings/edit.html', form=form)


"""
@admin.route('/ldap', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='update')
def ldap_edit():
    settings = Settings.query.first_or_404()
    form = LDAPForm(obj=settings)
    if form.validate_on_submit():
        form.populate_obj(settings)
        try:
            connection = ldap_con(form.ldap_host.data,
                                  form.ldap_port.data,
                                  form.ldap_bind_username.data,
                                  form.ldap_bind_password.data,
                                  domain_name=form.domain_name.data)
            if connection.bind():
                login_msg = f'Successful bind to ldap server'
            else:
                login_msg = f'Cannot bind to ldap server: {connection.last_error}'
            connection.unbind()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            if login_msg == 'Successful bind to ldap server':
                settings.save()
                flash('Settings saved successfully.', 'success')
            else:
                flash(f"*** Authentication Failed - {login_msg}", 'danger')
    return render_template('settings/ldap.html', form=form)
"""



@admin.route('/emails/new', methods=['GET', 'POST'])
def emails_new():
    email = SystemEmail()
    form = SystemEmailForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(email)
        except Exception as e:
            flash(f'{e}')
        else:
            email.save()
            flash('Created successfully.', 'success')
            return redirect(url_for('admin.emails'))
    return render_template('email/edit.html', form=form)


# EDIT ROUTES
@admin.route('/emails/edit/<int:id>', methods=['GET', 'POST'])
def emails_edit(id):
    email = SystemEmail.query.get_or_404(id)
    form = SystemEmailForm(obj=email)
    if form.validate_on_submit():
        try:
            form.populate_obj(email)
            email.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash(f'{email.name} has been updated successfully.', 'success')
            return redirect(url_for('admin.emails_edit', id=email.id))

    return render_template('email/edit.html',
                           form=form,
                           email=email
                           )


@admin.route('/users/<int:id>/delete', methods=['POST'])
@permission_required('admin.user', crud='delete')
def users_delete(id):
    user = User.query.get_or_404(id)
    try:
        user.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {user}', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/countries/<int:id>/delete', methods=['POST'])
@permission_required('admin.country', crud='delete')
def countries_delete(id):
    country = Country.query.get_or_404(id)
    try:
        country.delete()
    except Exception as e:
        flash(f'{e}', 'danger')
    flash(f'Successfully deleted {country.name}', 'success')
    return redirect(url_for('admin.countries'))


@admin.route('/countries/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.country', crud='update')
def countries_edit(id):
    country = Country.query.get_or_404(id)
    form = CountryForm(obj=country)
    if form.validate_on_submit():
        try:
            form.populate_obj(country)
            country.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash(f'{country.name} has been updated successfully.', 'success')
            return redirect(url_for('admin.countries_edit', id=country.id))

    return render_template('country/edit.html',
                           form=form,
                           country=country
                           )

@admin.route('/countries/new', methods=['GET', 'POST'])
@permission_required('admin.country', crud='create')
def countries_new():
    country = Country()
    form = CountryForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(country)
            country.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created.', 'success')
            return redirect(url_for('admin.countries'))
    return render_template('country/edit.html', form=form)


@admin.route('/countries/<int:id>/public-holidays/new', methods=['GET', 'POST'])
@permission_required('admin.public_holiday', crud='create')
def public_holiday_new(id):
    country = Country.query.get_or_404(id)
    holiday = PublicHoliday()
    form = PublicHolidayForm(obj=holiday)
    if form.validate_on_submit():
        try:
            form.populate_obj(holiday)
            holiday.country_id = id
            holiday.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Successfully created new public holiday', 'success')
            return redirect(url_for('admin.country', id=country.id))
    return render_template('country/edit_holiday.html',
                           form=form,
                           country=country)


@admin.route('/countries/<int:country_id>/public-holidays/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.public_holiday', crud='update')
def public_holiday_edit(country_id, id):
    country = Country.query.get_or_404(country_id)
    holiday = PublicHoliday.query.get_or_404(id)
    form = PublicHolidayForm(obj=holiday)
    if form.validate_on_submit():
        try:
            form.populate_obj(holiday)
            holiday.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Successfully updated', 'success')
            return redirect(url_for('admin.country', id=country.id))
    return render_template('country/edit_holiday.html',
                           form=form,
                           country=country,
                           holiday=holiday
                           )

@admin.route('/countries/<int:cid>/public-holiday/<int:id>/delete', methods=['POST'])
@permission_required('admin.public_holiday', crud='delete')
def public_holiday_delete(cid, id):
    holiday = PublicHoliday.query.get_or_404(id)
    try:
        holiday.delete()
    except Exception as e:
        flash(f'{e}', 'danger')
    return redirect(url_for('admin.country', id=cid))


@admin.route('/countries/<int:id>/public-holidays/bulk_delete', methods=['POST'])
@permission_required('admin.public_holiday', crud='delete')
def holidays_bulk_delete(id):
    country = Country.query.get(id)
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.utils.countries.tasks import delete_holidays
    delete_holidays.delay(ids)
    flash('{0} public holidays scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.country', id=country.id))


@admin.route('/countries/bulk_delete', methods=['POST'])
@permission_required('admin.country', crud='delete')
def countries_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.utils.countries.tasks import delete_countries
    delete_countries.delay(ids)
    flash('{0} countries scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.countries'))


@admin.route('/departments/new', methods=['GET', 'POST'])
@permission_required('admin.department', crud='create')
def departments_new():
    department = Department()
    form = NewDepartmentForm()
    if form.validate_on_submit():
        form.populate_obj(department)
        department.save()
        flash('Successfully created department', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('department/edit.html', form=form)


@admin.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.department', crud='update')
def departments_edit(id):
    department = Department.query.get(id)
    form = EditDepartmentForm(obj=department)
    if form.validate_on_submit():
        form.populate_obj(department)
        department.save()
        flash('Department has been saved successfully.', 'success')
        return redirect(url_for('admin.departments_edit', id=department.id))

    return render_template('department/edit.html', form=form, department=department)


@admin.route('/departments/bulk_delete', methods=['POST'])
@permission_required('admin.department', crud='delete')
def departments_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.department.tasks import delete_departments
    delete_departments.delay(ids)
    flash('{0} department(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.departments'))


@admin.route('/event-type/new', methods=['GET', 'POST'])
def event_type_new():
    event_type = EventType(active=True, hex_colour='#0066FF')
    form = EventTypeSettingsForm(obj=event_type)
    try:
        if form.validate_on_submit():
            #event_type = EventType(name=form.name.data, hex_colour=form.hex_colour.data)
            form.populate_obj(event_type)
            event_type.save()
            flash(f'Successfully created event type {event_type.name}', 'success')
            return redirect(url_for('admin.events'))
    except Exception as e:
        flash(f'{e}', 'danger')
    return render_template('event/type_edit.html', form=form)


@admin.route('/event-type/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.event_type', crud='update')
def event_type_edit(id):
    event_type = EventType.query.get(id)
    form = EventTypeSettingsForm(obj=event_type)
    if form.validate_on_submit():
        form.populate_obj(event_type)
        event_type.save()
        flash(f'Event Type {event_type.name} has been saved successfully.', 'success')
        return redirect(url_for('admin.events'))
    return render_template('event/type_edit.html', form=form, event_type=event_type)


@admin.route('/event-type/<int:id>/delete', methods=['POST'])
@permission_required('admin.event_type', crud='delete')
def event_type_delete(id):
    event_type = EventType.query.get(id)
    try:
        event_type.delete()
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {page.name}', 'success')
    return redirect(url_for('admin.events'))


@admin.route('/events/<int:id>/status/edit', methods=['GET', 'POST'])
def event_status_edit(id):
    event = Event.query.get(id)
    form = EventRequestsForm(obj=event)
    if form.validate_on_submit():
        form.populate_obj(event)
        event.save()
        flash('The status for the event request has been updated', 'success')
        return redirect(url_for('admin.events'))
    return render_template('event/status_edit.html', form=form, event=event)


@admin.route('/event-type/bulk_delete', methods=['POST'])
def event_type_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.event.tasks import delete_event_type
    delete_event_type.delay(ids)
    flash('{0} event type(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.events'))


@admin.route('/events/bulk_disable', methods=['POST'])
def event_bulk_disable():
    ids = request.form.get('checked-items').split(",")
    print(ids)
    print(type(ids))
    # stops circular import error
    from app.event.tasks import disable_event_type
    disable_event_type.delay(ids)
    flash('{0} event type(s) scheduled to be disabled.'.format(len(ids)), 'success')
    return redirect(url_for('admin.events'))


@admin.route('/events/bulk_enable', methods=['POST'])
def event_bulk_enable():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.event.tasks import enable_event_type
    enable_event_type.delay(ids)
    flash('{0} event type(s) scheduled to be enabled.'.format(len(ids)), 'success')
    return redirect(url_for('admin.events'))


@admin.route('/pages/bulk_disable', methods=['POST'])
def pages_bulk_disable():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.pages.tasks import disable_page
    disable_page.delay(ids)
    flash('{0} page(s) scheduled to be disabled.'.format(len(ids)), 'success')
    return redirect(url_for('admin.pages'))


@admin.route('/pages/bulk_enable', methods=['POST'])
def pages_bulk_enable():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.pages.tasks import enable_page
    enable_page.delay(ids)
    flash('{0} page(s) scheduled to be enabled.'.format(len(ids)), 'success')
    return redirect(url_for('admin.pages'))


@admin.route('/pages/bulk_delete', methods=['POST'])
def pages_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.pages.tasks import delete_page
    delete_page.delay(ids)
    flash('{0} page(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.pages'))


@admin.route('/users/new', methods=['GET', 'POST'])
@permission_required('admin.user', crud='create')
def users_new():
    user = User()
    form = NewUserForm(active=True, send_activation_account_email=True)
    try:
        if form.validate_on_submit():
            form.populate_obj(user)
            #TODO move annual allowance setup into succint method
            # that user.register can also use
            user.annual_entitlement = user.country.default_annual_allowance
            user.total_holiday_entitlement = user.annual_entitlement
            user.max_carry_over_days = user.country.default_carry_over_days
            user.days_left = user.total_holiday_entitlement
            user.save()
            if form.send_activation_account_email.data == True:
                # send activation email
                user = User.query.filter(User.email==form.email.data).first_or_404()
                from app.email import send_activation_email
                send_activation_email.delay(user)
            flash('Successfully created user', 'success')
            return redirect(url_for('admin.users'))
        else:
            for error in form.errors.items():
                print(error)
    except Exception as e:
        flash(f'{e}', 'danger')
    return render_template('user/edit.html', form=form)


@admin.route('/users/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='read')
def users_info(id):
    user = User.query.get(id)
    return render_template('user/info.html', user=user)


@admin.route('/roles/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.role', crud='read')
def roles_info(id):
    role = Role.query.get(id)
    return render_template('role/info.html', role=role)


@admin.route('/permissions/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.permission', crud='read')
def permissions_info(id):
    perm = Permission.query.get(id)
    return render_template('permission/info.html', perm=perm)


@admin.route('/departments/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.department', crud='read')
def departments_info(id):
    dept = Department.query.get(id)
    return render_template('department/info.html', dept=dept)


@admin.route('/events/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.event_type', crud='read')
def event_type_info(id):
    etype = EventType.query.get(id)
    return render_template('event/info.html', etype=etype)


@admin.route('/pages/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.page', crud='read')
def pages_info(id):
    page = Page.query.get(id)
    return render_template('pages/info.html', page=page)


@admin.route('/emails/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='read')
def emails_info(id):
    email = SystemEmail.query.get(id)
    return render_template('email/info.html', email=email)


@admin.route('/settings', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='read')
def settings():
    settings = Settings.query.first_or_404(id)
    return render_template('settings/info.html', settings=settings)


@admin.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='update')
def users_edit(id):
    user = User.query.get(id)
    form = NewUserForm(obj=user, departments=user.department)
    if form.validate_on_submit():
        """
        if User.is_last_admin(user):
            flash('You are the last admin, you cannot do that.', 'danger')
            return redirect(url_for('admin.users'))
            """
        if form.authoriser.data == user:
            abort(400)
            # this is caught by validators
            # user cannot assign themselves as authorisers

        if not user.username:
            user.username = None

        form.populate_obj(user)
        #[user.department] = form.departments.data

        try:
            user.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('User has been saved successfully.', 'success')
        return redirect(url_for('admin.users_edit', id=user.id))
    return render_template('user/edit.html',
                           form=form,
                           user=user)


@admin.route('/roles/bulk_delete', methods=['POST'])
def roles_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import delete_roles
    delete_roles.delay(ids)
    flash('{0} role(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/users/bulk_delete', methods=['POST'])
def users_bulk_delete():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import delete_users
    delete_users.delay(ids)
    flash('{0} user(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/bulk_lock', methods=['POST'])
def users_bulk_lock():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import disable_user_login
    disable_user_login.delay(ids)
    flash('{0} user(s) scheduled to be disabled for login.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/bulk_unlock', methods=['POST'])
def users_bulk_unlock():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import enable_user_login
    enable_user_login.delay(ids)
    flash('{0} user(s) scheduled for activation.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/bulk_password_reset', methods=['POST'])
def users_bulk_password_reset():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import reset_users_passwords
    reset_users_passwords.delay(ids)
    flash('{0} user(s) scheduled to be sent a password reset email.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/password_reset/<int:id>', methods=['GET', 'POST'])
def password_reset(id):
    user = User.query.get(id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.password = User.encrypt_password(form.password.data)
            user.save()
        except Exception as e:
            flash(e, 'danger')
        else:
            flash('The password for this user has been reset', 'success')
            return redirect(url_for('admin.users_edit', id=user.id))
    return render_template('user/reset_password.html', form=form, user=user)


@admin.route('/permissions/new', methods=['GET', 'POST'])
def permissions_new():
    permission = Permission()
    form = PermissionForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(permission)
        except Exception as e:
            flash(f'{e}')
        else:
            permission.save()
            flash('Created successfully.', 'success')
            return redirect(url_for('admin.permissions'))
    return render_template('permission/edit.html', form=form)


@admin.route('/permissions/edit/<int:id>', methods=['GET', 'POST'])
def permissions_edit(id):
    permission = Permission.query.get_or_404(id)
    form = PermissionForm(obj=permission)
    if form.validate_on_submit():
        try:
            form.populate_obj(permission)
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            permission.save()
            flash('Updated successfully.', 'success')
            return redirect(url_for('admin.permissions'))
    return render_template('permission/edit.html', form=form, permission=permission)


@admin.route('/roles/new', methods=['GET', 'POST'])
def roles_new():
    role = Role()
    form = RoleForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(role)
        except Exception as e:
            flash(f'{e}')
        else:
            role.save()
            flash('Created successfully.', 'success')
            return redirect(url_for('admin.roles'))
    return render_template('role/edit.html', form=form)


@admin.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
def roles_edit(id):
    role = Role.query.get(id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        try:
            form.populate_obj(role)
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            role.save()
            flash('Updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
    return render_template('role/edit.html', form=form, role=role)


@admin.route('/backup/export/csv/', methods=['POST'])
@permission_required('admin.settings', crud='read')
def export_csv_backup():
    table = request.form["table_name"]
    output = dump_csv(name=table)
    settings = Settings.query.first()

    return send_file(
        output,
        as_attachment=True,
        max_age=-1,
        download_name="{name}-{table}.csv".format(
            name=settings.site_name, table=table
        ),
    )


@admin.route('/export_selected/csv/<string:table>', methods=['POST'])
def export_selected_csv(table):
    if request.form.get('checked-items') == '':
        flash('No items selected', 'danger')
        return redirect(request.referrer)
    ids = request.form.get('checked-items').split(",")
    # if user does not have read permission for current table, abort
    if not current_user.permission('admin.' + str(table), crud='read'):
        abort(403)
    output = dump_table_selected_ids(table, ids)

    settings = Settings.query.first()

    return send_file(
        output,
        as_attachment=True,
        max_age=-1,
        download_name="{name}-{table}.csv".format(
            name=settings.site_name, table=table
        ),
    )


@admin.route("/import/zip", methods=["POST"])
@permission_required('admin.settings', crud='create')
@permission_required('admin.settings', crud='update')
@permission_required('admin.settings', crud='delete')
def import_zip():
    backup = request.files["zip_file"]
    try:
        import_zipfile(backup)
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash('Successfully imported data from zip file', 'success')
    return redirect(url_for("admin.backup"))


@admin.route("/import/csv", methods=["POST"])
@permission_required('admin.settings', crud='create')
def import_csv():
    #csv_type = request.form["csv_type"]
    # Try really hard to load data in properly no matter what nonsense Excel gave you
    raw = request.files["csv_file"].stream.read()
    model_str = request.form["csv_type"]
    model_name = get_class_by_tablename(model_str)
    try:
        csvdata = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csvdata = raw.decode("cp1252")
        except UnicodeDecodeError:
            csvdata = raw.decode("latin-1")
    csvfile = StringIO(csvdata, newline='')

    '''
    loaders = {
        "challenges": load_challenges_csv,
        "users": load_users_csv,
        "teams": load_teams_csv,
    }
    #loader = loaders[csv_type]
    '''
    #loader = load_users_csv
    reader = csv.DictReader(x.replace('\0', '') for x in csvfile)
    success = load_csv(model_name, reader)
    if success is True:
        return redirect(request.referrer)
    else:
        return jsonify(success), 500


@admin.route("/backup", methods=["GET", "POST"])
@permission_required('admin.settings', crud='read')
def backup():
    forms = {
        'export_csv_form': ExportCSVForm(),
        'import_csv_form': ImportCSVForm(),
        'import_zip_form': ImportZipForm()
    }
    return render_template("settings/backup.html", **forms)


@admin.route('/export_zip', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='read')
def export_zip():
    backup = export_zipfile()
    settings = Settings.query.first()
    return send_file(backup, as_attachment=True, max_age=-1,
                     download_name="{name}.zip".format(name=settings.site_name))


@admin.route('/test-email-config/<int:id>', methods=['POST'])
def test_email_config(id):
    from app.email import test_email
    return test_email(id)


@admin.route("/celerystatus", methods=["GET", "POST"])
def celery_status():
    # avoid circular import
    from app.celery import celery
    celery_inspect = celery.control.inspect()
    try:
        celery_running = True if celery_inspect.ping() else False
    except Exception:
        # catching Exception is bad, and just catching ConnectionError
        # from redis is also bad because you can run celery with other
        # brokers as well.
        celery_running = False

    return jsonify(celery_running=celery_running, status=200)