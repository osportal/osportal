#from app.admin.routes import admin
from flask_login import current_user


def admin_settings_menu(user):
    results = [
        ('admin.users', 'Users', 'fa fa-users'),
        ('admin.roles', 'Roles', 'fa fa-hammer'),
        ('admin.permissions', 'Permissions', 'fa fa-key'),
        ('admin.departments', 'Departments', 'fa fa-sitemap'),
        ('admin.events', 'Events', 'fa fa-plane'),
        ('admin.pages', 'Pages', 'fa fa-file'),
        ('admin.emails', 'Emails', 'fa fa-envelope'),
        ('admin.countries', 'Countries', 'fa fa-globe'),
        ('admin.settings', 'Settings', 'fa fa-cogs')
    ]
    for result in results:
        view = result[0]
        if view=='admin.users' \
                and current_user.permission('admin.user', crud='read'):
                    yield result
        if view=='admin.roles' \
                and current_user.permission('admin.role', crud='read'):
                    yield result
        if view=='admin.permissions' \
                and current_user.permission('admin.permission', crud='read'):
                    yield result
        if view == 'admin.departments' \
                and current_user.permission('admin.department', crud='read'):
                    yield result
        if view == 'admin.events' \
                and current_user.permission('admin.event_type', crud='read'):
                    yield result
        if (view=='admin.pages') \
                and current_user.permission('admin.page', crud='read'):
                    yield result
        if (view=='admin.emails') \
                and current_user.permission('admin.system_email', crud='read'):
                    yield result
        if (view=='admin.countries') \
                and current_user.permission('admin.country', crud='read'):
                    yield result
        if view=='admin.settings' \
                and current_user.permission('admin.settings', crud='read'):
                    yield result


def admin_user_sidebar(user):
    results = [
        ('admin.users', 'Manage', ''),
        ('admin.users_new', 'New User', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.users' \
            and current_user.permission('admin.user', crud='read'):
                yield result
        if view == 'admin.users_new' \
            and current_user.permission('admin.user', crud='create'):
                yield result


def admin_permission_sidebar(user):
    results = [
        ('admin.permissions', 'Manage', ''),
        ('admin.permissions_new', 'New Permission', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.permissions' \
            and current_user.permission('admin.permission', crud='read'):
                yield result
        if view == 'admin.permissions_new' \
            and current_user.permission('admin.permission', crud='create'):
                yield result


def admin_role_sidebar(user):
    results = [
        ('admin.roles', 'Manage', ''),
        ('admin.roles_new', 'New Role', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.roles' \
            and current_user.permission('admin.role', crud='read'):
                yield result
        if view == 'admin.roles_new' \
            and current_user.permission('admin.role', crud='create'):
                yield result


def admin_department_sidebar(user):
    results = [
        ('admin.departments', 'Manage', ''),
        ('admin.departments_new', 'New Department', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.departments' \
            and current_user.permission('admin.department', crud='read'):
                yield result
        if view == 'admin.departments_new' \
            and current_user.permission('admin.department', crud='create'):
                yield result


def admin_event_sidebar(user):
    results = [
        ('admin.events', 'Manage Types', ''),
        ('admin.event_type_new', 'New Type', ''),
        ('admin.event_requests', 'Manage Requests', ''),
    ]
    for result in results:
        view = result[0]
        if (view=='admin.events' or view=='admin.event_requests') \
            and current_user.permission('admin.event', crud='read'):
                yield result
        if view == 'admin.event_type_new' \
            and current_user.permission('admin.event_type', crud='create'):
                yield result


def admin_pages_sidebar(user):
    results = [
        ('admin.pages', 'Manage', ''),
        ('admin.pages_new', 'New Page', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.pages' \
            and current_user.permission('admin.page', crud='read'):
                yield result
        if view == 'admin.pages_new' \
            and current_user.permission('admin.page', crud='create'):
                yield result


def admin_emails_sidebar(user):
    results = [
        ('admin.emails', 'Manage', ''),
        ('admin.emails_new', 'New Email', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.emails' \
            and current_user.permission('admin.system_email', crud='read'):
                yield result
        if view == 'admin.emails_new' \
            and current_user.permission('admin.system_email', crud='create'):
                yield result

def admin_country_sidebar(user):
    results = [
        ('admin.countries', 'Manage', ''),
        ('admin.countries_new', 'New Country', '')
    ]
    # TODO need to decide on whether to show then edit settings etc.
    for result in results:
        view = result[0]
        if view=='admin.countries' \
            and current_user.permission('admin.countries', crud='read'):
                yield result
        if view=='admin.countries_new' \
            and current_user.permission('admin.countries_new', crud='create'):
                yield result


def admin_settings_sidebar(user):
    results = [
        ('admin.settings', 'Manage', ''),
        ('admin.backup', 'Import/Export Data', ''),
        #('admin.ldap_edit', 'LDAP Auth', ''),
    ]
    # TODO need to decide on whether to show then edit settings etc.
    for result in results:
        view = result[0]
        if view == 'admin.settings' \
            and current_user.permission('admin.settings', crud='read'):
                yield result
        #if view == 'admin.ldap_edit' \
        #    and current_user.permission('admin.settings', crud='read'):
        #        yield result
        if view == 'admin.backup' \
            and current_user.permission('admin.settings', crud='read'):
                yield result


def update_admin_jinja_globals(app):
    app.jinja_env.globals.update(admin_settings_menu=admin_settings_menu)
    app.jinja_env.globals.update(admin_user_sidebar=admin_user_sidebar)
    app.jinja_env.globals.update(admin_role_sidebar=admin_role_sidebar)
    app.jinja_env.globals.update(admin_permission_sidebar=admin_permission_sidebar)
    app.jinja_env.globals.update(admin_department_sidebar=admin_department_sidebar)
    app.jinja_env.globals.update(admin_event_sidebar=admin_event_sidebar)
    app.jinja_env.globals.update(admin_pages_sidebar=admin_pages_sidebar)
    app.jinja_env.globals.update(admin_emails_sidebar=admin_emails_sidebar)
    app.jinja_env.globals.update(admin_country_sidebar=admin_country_sidebar)
    app.jinja_env.globals.update(admin_settings_sidebar=admin_settings_sidebar)
