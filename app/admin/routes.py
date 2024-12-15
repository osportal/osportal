from celery import __version__ as celery_version
# for plugins
from collections import namedtuple
from datetime import datetime
import json
import os
#
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
                             SiteForm,
                             EnttForm,
                             SettingsForm, PageForm, LeaveTypeSettingsForm,
                             LeaveRequestsForm, ImportCSVForm, ExportCSVForm,
                             ImportZipForm, PublicHolidayForm, CountryForm,
                             EmailForm, ResetPasswordForm,
                             PublicHolidayGroupForm,
                             PublicHolidayYearForm, AdminPostForm)
from app.admin.models import Dashboard, Settings, Email
from app.admin.utils import get_settings_value
from app.department.models import Department, DepartmentMembers
from app.extensions import db
from app.models import (Site, Country,
                        Entt,
                        PublicHolidayGroup, PublicHoliday,
                        get_class_by_tablename)
from app.leave.models import Leave, LeaveType
from app.pages.models import Page
from app.posts.models import Post
#from app.user.auth import ldap_con
from app.user.decorators import permission_required
from app.user.models import User, Role, Permission
from app.user.forms import RegistrationForm
from app.utils.csv import load_csv, dump_csv, dump_table_selected_ids
from app.utils.util_sqlalchemy import ResourceMixin
from app.utils.zip import export_zipfile, import_zipfile


admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.before_request
@login_required
def before_request():
    """ Protect all admin endpoints """
    pass


@admin.route('/')
@admin_read_required()
def dashboard():
    stats = {
        "celery_version": celery_version,
        "flask_version": flask_version,
        "group_and_count_posts": Dashboard.group_and_count_posts(),
        "group_and_count_pages": Dashboard.group_and_count_pages(),
        "group_and_count_users": Dashboard.group_and_count_users(),
        "group_and_count_roles": Dashboard.group_and_count_roles(),
        "group_and_count_permissions": Dashboard.group_and_count_permissions(),
        "group_and_count_departments": Dashboard.group_and_count_departments(),
        "group_and_count_sites": Dashboard.group_and_count_sites(),
        "group_and_count_entts": Dashboard.group_and_count_entts(),
        "group_and_count_leave_types": Dashboard.group_and_count_leave_types(),
        "group_and_count_emails": Dashboard.group_and_count_emails(),
        "group_and_count_countries": Dashboard.group_and_count_countries(),
        "group_and_count_holiday_groups": Dashboard.group_and_count_holiday_groups(),
        "group_and_count_plugins": get_valid_plugins()
    }
    return render_template('admin_dashboard.html', **stats)


@admin.route('/emails', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/emails/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.email', crud='read')
def emails(page):
    search_form = SearchForm()
    sort_by = Email.sort_by(request.args.get('sort', 'name'),
                              request.args.get('direction', 'asc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
    paginated_emails = Email.query \
        .filter(Email.search((request.args.get('q', text(''))))) \
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
def country(id, page):
    country = Country.query.get_or_404(id)
    return render_template('country/country.html',
                           country=country,
                           )


@admin.route('/sites', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/sites/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.site', crud='read')
def sites(page):
    search_form = SearchForm()

    sort_by = Site.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_sites = Site.query \
        .filter(Site.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('site/index.html',
                           form=search_form,
                           sites=paginated_sites)



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


@admin.route('/entitlement-templates', defaults={'page':1}, methods=['GET', 'POST'])
@admin.route('/entitlement-templates/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.entt', crud='read')
def entts(page):
    search_form = SearchForm()

    sort_by = Entt.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_entts = Entt.query \
        .filter(Entt.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('entt/index.html', form=search_form, entts=paginated_entts)


@admin.route('/leave-types', defaults={'page':1}, methods=['GET', 'POST'])
@admin.route('/leave-types/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.leave_type', crud='read')
def leave_types(page):
    search_form = SearchForm()

    sort_by = LeaveType.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_ltypes = LeaveType.query \
        .filter(LeaveType.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('leave_type/index.html', leave_types=paginated_ltypes)


@admin.route('/leaves', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/leaves/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.leave', crud='read')
def leaves(page):
    leaves = Leave.query \
            .paginate(page, get_settings_value('items_per_admin_page'), False)
    return render_template('leave/index.html', leaves=leaves)


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
    # first order value is in double quotes because 'create' is keyword in postgres
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
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created.', 'success')
            return redirect(url_for('admin.pages'))
    else:
        for error in form.errors.items():
            print(error)
    return render_template('pages/edit.html', form=form)


@admin.route('/pages/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.page', crud='update')
def pages_edit(id):
    page = Page.query.get(id)
    form = PageForm(obj=page)
    if form.validate_on_submit():
        try:
            form.populate_obj(page)
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
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


@admin.route('/posts', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/posts/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.post', crud='read')
def posts(page):
    search_form = SearchForm()
    sort_by = Post.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_posts = Post.query \
        .filter(Post.search((request.args.get('q', text(''))))) \
        .order_by(Post.is_pin.desc(), text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('post/index.html',
                           form=search_form,
                           posts=paginated_posts)


@admin.route('/posts/new', methods=['GET', 'POST'])
@permission_required('admin.post', crud='create')
def posts_new():
    post = Post()
    form = AdminPostForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(post)
            post.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created.', 'success')
            return redirect(url_for('admin.posts'))
    else:
        for error in form.errors.items():
            print(error)
    return render_template('post/edit.html', form=form)


@admin.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.post', crud='update')
def posts_edit(id):
    post = Post.query.get_or_404(id)
    form = AdminPostForm(obj=post)
    if form.validate_on_submit():
        try:
            form.populate_obj(post)
            post.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Successfully updated.', 'success')
            return redirect(url_for('admin.posts'))
    return render_template('post/edit.html', form=form, post=post)


@admin.route('/posts/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.post', crud='read')
def posts_info(id):
    post = Post.query.get(id)
    return render_template('post/info.html', post=post)


@admin.route('/posts/<int:id>/delete', methods=['POST'])
@permission_required('admin.post', crud='delete')
def posts_delete(id):
    post = Post.query.get_or_404(id)
    try:
        post.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {post.name}', 'success')
    return redirect(url_for('admin.posts'))


@admin.route('/settings/edit', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='update')
def settings_edit():
    url = url_for('admin.settings')
    settings = Settings.query.first_or_404()
    form = SettingsForm(obj=settings)
    if form.validate_on_submit():
        form.populate_obj(settings)
        settings.save()
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('admin.settings'))
    return render_template('settings/edit.html', form=form, url=url)


@admin.route('/emails/new', methods=['GET', 'POST'])
@permission_required('admin.email', crud='create')
def emails_new():
    email = Email()
    form = EmailForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(email)
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            email.save()
            flash('Created successfully.', 'success')
            return redirect(url_for('admin.emails_info', id=email.id))
    return render_template('email/edit.html', form=form)


@admin.route('/emails/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.email', crud='update')
def emails_edit(id):
    email = Email.query.get_or_404(id)
    form = EmailForm(obj=email)
    if form.validate_on_submit():
        try:
            form.populate_obj(email)
            email.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'{email.name} has been updated successfully.', 'success')
            return redirect(url_for('admin.emails_edit', id=email.id))

    return render_template('email/edit.html',
                           form=form,
                           email=email
                           )


@admin.route('/emails/<int:id>/delete', methods=['POST'])
@permission_required('admin.email', crud='delete')
def emails_delete(id):
    email = Email.query.get_or_404(id)
    try:
        email.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted email {email.name}', 'success')
    return redirect(url_for('admin.emails'))


@admin.route('/users/<int:id>/delete', methods=['POST'])
@permission_required('admin.user', crud='delete')
def users_delete(id):
    user = User.query.get_or_404(id)
    if user.locked:
        abort(403)
    try:
        if user.is_last_superuser():
            raise Exception('Cannot delete the last remaining superuser')
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
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
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
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
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
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created.', 'success')
            return redirect(url_for('admin.countries'))
    return render_template('country/edit.html', form=form)


@admin.route('/sites/new', methods=['GET', 'POST'])
@permission_required('admin.site', crud='create')
def sites_new():
    site = Site()
    form = SiteForm(obj=site)
    if form.validate_on_submit():
        try:
            form.populate_obj(site)
            site.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Successfully created new site', 'success')
            return redirect(url_for('admin.sites_info', id=site.id))
    return render_template('site/edit.html',
                           form=form,
                           site=site)


@admin.route('/sites/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.site', crud='update')
def sites_edit(id):
    site = Site.query.get_or_404(id)
    form = SiteForm(obj=site)
    if form.validate_on_submit():
        try:
            form.populate_obj(site)
            site.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Successfully updated', 'success')
            return redirect(url_for('admin.sites_info', id=site.id))
    return render_template('site/edit.html',
                           form=form,
                           site=site
                           )


@admin.route('/sites/<int:id>/delete', methods=['POST'])
@permission_required('admin.site', crud='delete')
def sites_delete(id):
    site = Site.query.get_or_404(id)
    try:
        site.delete()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted', 'success')
    return redirect(url_for('admin.sites'))


@admin.route('/public-holiday-groups/<int:id>/public-holidays/new', methods=['GET', 'POST'])
@permission_required('admin.public_holiday', crud='create')
def public_holiday_new(id):
    group = PublicHolidayGroup.query.get_or_404(id)
    holiday = PublicHoliday()
    form = PublicHolidayForm(obj=holiday)
    if form.validate_on_submit():
        try:
            form.populate_obj(holiday)
            holiday.group_id = id
            holiday.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Successfully created new public holiday', 'success')
            return redirect(url_for('admin.public_holiday_groups_info', id=group.id))
    return render_template('public-holiday/edit.html',
                           form=form,
                           group=group)


@admin.route('/public-holiday-groups/<int:group_id>/public-holidays/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.public_holiday', crud='update')
def public_holiday_edit(group_id, id):
    group = PublicHolidayGroup.query.get_or_404(group_id)
    holiday = PublicHoliday.query.get_or_404(id)
    form = PublicHolidayForm(obj=holiday)
    if form.validate_on_submit():
        try:
            form.populate_obj(holiday)
            holiday.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Successfully updated', 'success')
            return redirect(url_for('admin.public_holiday_groups_info', id=group.id))
    return render_template('public-holiday/edit.html',
                           form=form,
                           group=group,
                           holiday=holiday
                           )


@admin.route('/public-holiday-groups/<int:gid>/public-holiday/<int:id>/delete', methods=['POST'])
@permission_required('admin.public_holiday', crud='delete')
def public_holiday_delete(gid, id):
    holiday = PublicHoliday.query.get_or_404(id)
    try:
        holiday.delete()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {holiday.name}', 'success')
    return redirect(url_for('admin.public_holiday_groups_info', id=gid))


@admin.route('/public-holiday-groups', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/public-holiday-groups/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.public_holiday_group', crud='read')
def public_holiday_groups(page):
    search_form = SearchForm()

    sort_by = PublicHolidayGroup.sort_by(request.args.get('sort', 'created_at'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_groups = PublicHolidayGroup.query \
        .filter(PublicHolidayGroup.search((request.args.get('q', text(''))))) \
        .order_by(text(order_values)) \
        .paginate(page, get_settings_value('items_per_admin_page'), True)

    return render_template('public-holiday-group/index.html',
                           form=search_form,
                           groups=paginated_groups)


@admin.route('/public-holiday-groups/new', methods=['GET', 'POST'])
@permission_required('admin.public_holiday_group', crud='create')
def public_holiday_groups_new():
    group = PublicHolidayGroup()
    form = PublicHolidayGroupForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(group)
            group.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Successfully created Public Holiday Group', 'success')
            return redirect(url_for('admin.public_holiday_groups'))
    return render_template('public-holiday-group/edit.html', form=form)


@admin.route('/public-holiday-groups/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.public_holiday_group', crud='update')
def public_holiday_groups_edit(id):
    group = PublicHolidayGroup.query.get(id)
    form = PublicHolidayGroupForm(obj=group)
    if form.validate_on_submit():
        try:
            form.populate_obj(group)
            group.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Saved successfully.', 'success')
            return redirect(url_for('admin.public_holiday_groups_info', id=group.id))
    return render_template('public-holiday-group/edit.html', form=form, group=group)


@admin.route('/public-holiday-groups/<int:id>/delete', methods=['POST'])
@permission_required('admin.public_holiday_group', crud='delete')
def public_holiday_groups_delete(id):
    group = PublicHolidayGroup.query.get_or_404(id)
    try:
        group.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted group {group.name}', 'success')
    return redirect(url_for('admin.public_holiday_groups'))


@admin.route('/public-holiday-groups/<int:id>', defaults={'page': 1}, methods=['GET', 'POST'])
@admin.route('/public-holiday-groups/<int:id>/page/<int:page>', methods=['GET', 'POST'])
@permission_required('admin.public_holiday_group', crud='read')
def public_holiday_groups_info(id, page):
    group = PublicHolidayGroup.query.get_or_404(id)
    list_years = PublicHoliday.unique_years_by_group(group.id)
    current_year = datetime.today().year
    paginated_holidays = None
    form = PublicHolidayYearForm()
    dropdown_year = request.args.get('year')
    if list_years:
        if not dropdown_year:
            dropdown_year = list_years[0]
        form.year.choices = list_years
        paginated_holidays = PublicHoliday.query \
                .filter(PublicHoliday.group_id==group.id,
                        PublicHoliday.filter_year(dropdown_year)) \
                .paginate(page, get_settings_value('items_per_admin_page'), True)
    return render_template('public-holiday-group/info.html',
                           form=form,
                           group=group,
                           years=list_years,
                           dropdown_year=dropdown_year,
                           current_year=current_year,
                           paginated_holidays=paginated_holidays)


@admin.route('/departments/new', methods=['GET', 'POST'])
@permission_required('admin.department', crud='create')
def departments_new():
    department = Department()
    form = NewDepartmentForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(department)
            department.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Successfully created department', 'success')
            return redirect(url_for('admin.departments'))
    return render_template('department/edit.html', form=form)


@admin.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.department', crud='update')
def departments_edit(id):
    department = Department.query.get(id)
    form = EditDepartmentForm(obj=department)
    if form.validate_on_submit():
        try:
            form.populate_obj(department)
            department.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Department has been saved successfully.', 'success')
            return redirect(url_for('admin.departments_edit', id=department.id))
    return render_template('department/edit.html', form=form, department=department)


@admin.route('/departments/<int:id>/delete', methods=['POST'])
@permission_required('admin.department', crud='delete')
def departments_delete(id):
    dept = Department.query.get_or_404(id)
    try:
        dept.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted department {dept.name}', 'success')
    return redirect(url_for('admin.departments'))


@admin.route('/entitlement-templates/new', methods=['GET', 'POST'])
@permission_required('admin.entt', crud='create')
def entt_new():
    entt = Entt()
    form = EnttForm(obj=entt)
    if form.validate_on_submit():
        try:
            form.populate_obj(entt)
            entt.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created {entt.name}', 'success')
            return redirect(url_for('admin.entts'))
    return render_template('entt/edit.html', form=form)


@admin.route('/entitlement-templates/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.entt', crud='update')
def entt_edit(id):
    entt = Entt.query.get(id)
    form = EnttForm(obj=entt)
    if form.validate_on_submit():
        form.populate_obj(entt)
        entt.save()
        flash(f'Successfully updated {entt.name}', 'success')
        return redirect(url_for('admin.entts'))
    return render_template('entt/edit.html', form=form, entt=entt)


@admin.route('/entitlement-template/<int:id>/delete', methods=['POST'])
@permission_required('admin.entt', crud='delete')
def entt_delete(id):
    entt = Entt.query.get(id)
    try:
        entt.delete()
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {entt.name}', 'success')
    return redirect(url_for('admin.entts'))


@admin.route('/leave-type/new', methods=['GET', 'POST'])
@permission_required('admin.leave_type', crud='create')
def leave_type_new():
    leave_type = LeaveType(active=True, hex_colour='#0066FF', max_days=14)
    form = LeaveTypeSettingsForm(obj=leave_type)
    if form.validate_on_submit():
        try:
            form.populate_obj(leave_type)
            leave_type.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created {leave_type.name}', 'success')
            return redirect(url_for('admin.leave_types'))
    return render_template('leave_type/edit.html', form=form)


@admin.route('/leave-type/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.leave_type', crud='update')
def leave_type_edit(id):
    leave_type = LeaveType.query.get(id)
    form = LeaveTypeSettingsForm(obj=leave_type)
    if form.validate_on_submit():
        form.populate_obj(leave_type)
        leave_type.save()
        flash(f'Successfully updated {leave_type.name}', 'success')
        return redirect(url_for('admin.leave_types'))
    return render_template('leave_type/edit.html', form=form, leave_type=leave_type)


@admin.route('/leave-type/<int:id>/delete', methods=['POST'])
@permission_required('admin.leave_type', crud='delete')
def leave_type_delete(id):
    leave_type = LeaveType.query.get(id)
    try:
        leave_type.delete()
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted {leave_type.name}', 'success')
    return redirect(url_for('admin.leave_types'))


@admin.route('/leaves/<int:id>/status/edit', methods=['GET', 'POST'])
@permission_required('admin.leave', crud='update')
def leave_status_edit(id):
    leave = Leave.query.get(id)
    form = LeaveRequestsForm(obj=leave)
    if form.validate_on_submit():
        form.populate_obj(leave)
        leave.save()
        flash('The status for the leave request has been updated', 'success')
        return redirect(url_for('admin.leaves'))
    return render_template('leave/status_edit.html', form=form, leave=leave)


@admin.route('/<table>/bulk_delete', methods=['POST'])
def bulk_delete(table):
    if not current_user.permission('admin.'+table, crud='delete'):
        abort(403)
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.tasks import delete_obj
    delete_obj.delay(table, ids)
    flash('{0} item(s) scheduled to be deleted.'.format(len(ids)), 'success')
    return redirect(request.referrer)


@admin.route('/<table>/bulk_disable', methods=['POST'])
def bulk_disable(table):
    if not current_user.permission('admin.'+table, crud='update'):
        abort(403)
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.tasks import disable_obj
    disable_obj.delay(table, ids)
    flash('{0} item(s) scheduled to be disabled.'.format(len(ids)), 'success')
    return redirect(request.referrer)


@admin.route('/<table>/bulk_enable', methods=['POST'])
def bulk_enable(table):
    if not current_user.permission('admin.'+table, crud='update'):
        abort(403)
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.tasks import enable_obj
    enable_obj.delay(table, ids)
    flash('{0} item(s) scheduled to be enabled.'.format(len(ids)), 'success')
    return redirect(request.referrer)


@admin.route('/users/new', methods=['GET', 'POST'])
@permission_required('admin.user', crud='create')
def users_new():
    user = User()
    form = NewUserForm(active=True, send_activation_account_email=True)
    if form.validate_on_submit():
        try:
            form.populate_obj(user)
            #TODO move annual allowance setup into succint method
            # that user.register can also use
            #user.annual_entitlement = user.country.default_annual_allowance
            #user.days_left = user.annual_entitlement
            user.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            if form.send_activation_account_email.data == True:
                # send activation email
                user = User.query.filter(User.email==form.email.data).first_or_404()
                from app.email import send_activation_email
                send_activation_email.delay(user)
            flash('Successfully created user', 'success')
            return redirect(url_for('admin.users'))
    return render_template('user/edit.html', form=form)


@admin.route('/users/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='read')
def users_info(id):
    user = User.query.get_or_404(id)
    url = url_for('admin.users_edit', id=user.id)
    return render_template('user/info.html', user=user, url=url)


@admin.route('/roles/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.role', crud='read')
def roles_info(id):
    role = Role.query.get_or_404(id)
    return render_template('role/info.html', role=role)


@admin.route('/permissions/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.permission', crud='read')
def permissions_info(id):
    perm = Permission.query.get_or_404(id)
    return render_template('permission/info.html', perm=perm)


@admin.route('/sites/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.site', crud='read')
def sites_info(id):
    site = Site.query.get_or_404(id)
    return render_template('site/info.html', site=site)


@admin.route('/departments/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.department', crud='read')
def departments_info(id):
    dept = Department.query.get_or_404(id)
    return render_template('department/info.html', dept=dept)


@admin.route('/entitlement-templates/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.entt', crud='read')
def entt_info(id):
    entt = Entt.query.get_or_404(id)
    return render_template('entt/info.html', entt=entt)


@admin.route('/leaves/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.leave_type', crud='read')
def leave_type_info(id):
    ltype = LeaveType.query.get_or_404(id)
    return render_template('leave_type/info.html', ltype=ltype)


@admin.route('/pages/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.page', crud='read')
def pages_info(id):
    page = Page.query.get_or_404(id)
    return render_template('pages/info.html', page=page)


@admin.route('/emails/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='read')
def emails_info(id):
    email = Email.query.get_or_404(id)
    return render_template('email/info.html', email=email)


@admin.route('/settings', methods=['GET', 'POST'])
@permission_required('admin.settings', crud='read')
def settings():
    url = url_for('admin.settings_edit')
    settings = Settings.query.first_or_404(id)
    return render_template('settings/info.html', settings=settings, url=url)


@admin.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='update')
def users_edit(id):
    user = User.query.get_or_404(id)
    url = url_for('admin.users_info', id=user.id)
    if user.locked:
        abort(403)
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
                           user=user,
                           url=url)


@admin.route('/users/bulk_welcome_email', methods=['POST'])
@permission_required('admin.user', crud='update')
def users_bulk_welcome_email():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import send_welcome_email
    send_welcome_email.delay(ids)
    flash('{0} user(s) scheduled to be sent a welcome email.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/bulk_password_reset', methods=['POST'])
@permission_required('admin.user', crud='update')
def users_bulk_password_reset():
    ids = request.form.get('checked-items').split(",")
    # stops circular import error
    from app.user.tasks import reset_users_passwords
    reset_users_passwords.delay(ids)
    flash('{0} user(s) scheduled to be sent a password reset email.'.format(len(ids)), 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/password_reset/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.user', crud='update')
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
@permission_required('admin.permission', crud='create')
def permissions_new():
    permission = Permission()
    form = PermissionForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(permission)
            permission.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Created successfully.', 'success')
            return redirect(url_for('admin.permissions'))
    return render_template('permission/edit.html', form=form)


@admin.route('/permissions/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('admin.permission', crud='update')
def permissions_edit(id):
    permission = Permission.query.get_or_404(id)
    form = PermissionForm(obj=permission)
    if form.validate_on_submit():
        try:
            form.populate_obj(permission)
            permission.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Updated successfully.', 'success')
            return redirect(url_for('admin.permissions'))
    return render_template('permission/edit.html', form=form, permission=permission)


@admin.route('/permissions/<int:id>/delete', methods=['POST'])
@permission_required('admin.permission', crud='delete')
def permissions_delete(id):
    p = Permission.query.get_or_404(id)
    try:
        '''
        use ResourceMixin directly to delete permission because
        permission also has delete attr and is in conflict with
        the delete() method
        '''
        ResourceMixin.delete(p)
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted permission {p.name}', 'success')
    return redirect(url_for('admin.permissions'))


@admin.route('/roles/new', methods=['GET', 'POST'])
@permission_required('admin.role', crud='create')
def roles_new():
    role = Role()
    form = RoleForm()
    if form.validate_on_submit():
        try:
            form.populate_obj(role)
            role.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash(f'Successfully created role {role.name}', 'success')
            return redirect(url_for('admin.roles'))
    return render_template('role/edit.html', form=form)


@admin.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('admin.role', crud='update')
def roles_edit(id):
    role = Role.query.get_or_404(id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        try:
            form.populate_obj(role)
            role.save()
        except (IntegrityError, PendingRollbackError) as e:
            db.session.rollback()
            flash(f'{e.orig.diag.message_detail}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'{e}', 'danger')
        else:
            flash('Updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
    return render_template('role/edit.html', form=form, role=role)


@admin.route('/roles/<int:id>/delete', methods=['POST'])
@permission_required('admin.role', crud='delete')
def roles_delete(id):
    role = Role.query.get_or_404(id)
    try:
        role.delete()
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'{e}', 'danger')
    else:
        flash(f'Successfully deleted role {role.name}', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/backup/export/csv/', methods=['POST'])
@permission_required('admin.data', crud='read')
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
@permission_required('admin.data', crud='create')
@permission_required('admin.data', crud='update')
@permission_required('admin.data', crud='delete')
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
@permission_required('admin.data', crud='create')
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
@permission_required('admin.data', crud='read')
def backup():
    forms = {
        'export_csv_form': ExportCSVForm(),
        'import_csv_form': ImportCSVForm(),
        'import_zip_form': ImportZipForm()
    }
    return render_template("settings/backup.html", **forms)


@admin.route('/export_zip', methods=['GET', 'POST'])
@permission_required('admin.data', crud='read')
def export_zip():
    backup = export_zipfile()
    settings = Settings.query.first()
    return send_file(backup, as_attachment=True, max_age=-1,
                     download_name="{name}.zip".format(name=settings.site_name))


@admin.route('/test-email-config/<int:id>', methods=['POST'])
@permission_required('admin.email', crud='read')
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


def get_valid_plugins():
    Plugin = namedtuple("Plugin", ["name", "route"])

    plugins_path = os.path.join(current_app.root_path, "plugins")
    plugin_directories = os.listdir(plugins_path)

    plugins = []

    for dir in plugin_directories:
        if os.path.isfile(os.path.join(plugins_path, dir, "config.json")):
            path = os.path.join(plugins_path, dir, "config.json")
            with open(path) as f:
                plugin_json_data = json.loads(f.read())
                if type(plugin_json_data) is list:
                    for plugin_json in plugin_json_data:
                        p = Plugin(
                            name=plugin_json.get("name"),
                            route=plugin_json.get("route"),
                        )
                        plugins.append(p)
                else:
                    p = Plugin(
                        name=plugin_json_data.get("name"),
                        route=plugin_json_data.get("route"),
                    )
                    plugins.append(p)
        elif os.path.isfile(os.path.join(plugins_path, dir, "config.html")):
            p = Plugin(name=dir, route="/admin/plugins/{}".format(dir))
            plugins.append(p)

    return plugins


@admin.route("/plugins", methods=["GET", "POST"])
@permission_required('admin.plugin', crud='read')
def plugins():
    plugins = get_valid_plugins()
    return render_template('plugin/index.html', plugins=plugins)
