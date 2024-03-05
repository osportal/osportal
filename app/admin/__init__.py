#from app.admin.routes import admin
from flask_login import current_user


def admin_settings_menu(user):
    results = [
        ('admin.users', 'Users', 'bi bi-people-fill'),
        ('admin.roles', 'Roles', 'bi bi-hammer'),
        ('admin.permissions', 'Permissions', 'bi bi-key-fill'),
        ('admin.departments', 'Departments', 'bi bi-diagram-3-fill'),
        ('admin.events', 'Events', 'bi bi-calendar-event'),
        ('admin.event_types', 'Event Types', 'bi bi-luggage'),
        ('admin.posts', 'Posts', 'bi bi-pin-angle-fill'),
        ('admin.pages', 'Pages', 'bi bi-file-earmark'),
        ('admin.emails', 'Emails', 'bi bi-envelope'),
        ('admin.countries', 'Countries', 'bi bi-globe'),
        ('admin.plugins', 'Plugins', 'bi bi-plugin'),
        ('admin.settings', 'Settings', 'bi bi-tools'),
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
                and current_user.permission('admin.event', crud='read'):
                    yield result
        if view == 'admin.event_types' \
                and current_user.permission('admin.event_type', crud='read'):
                    yield result
        if (view=='admin.posts') \
                and current_user.permission('admin.post', crud='read'):
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
        if (view=='admin.plugins') \
                and current_user.permission('admin.plugin', crud='read'):
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
        ('admin.events', 'Manage', ''),
    ]
    for result in results:
        view = result[0]
        if view=='admin.events' \
            and current_user.permission('admin.event', crud='read'):
                yield result


def admin_event_type_sidebar(user):
    results = [
        ('admin.event_types', 'Manage', ''),
        ('admin.event_type_new', 'New Type', ''),
    ]
    for result in results:
        view = result[0]
        if view=='admin.event_types' \
            and current_user.permission('admin.event_type', crud='read'):
                yield result
        if view == 'admin.event_type_new' \
            and current_user.permission('admin.event_type', crud='create'):
                yield result


def admin_post_sidebar(user):
    results = [
        ('admin.posts', 'Manage', ''),
        ('admin.posts_new', 'New Post', ''),
    ]
    for result in results:
        view = result[0]
        if view == 'admin.posts' \
            and current_user.permission('admin.post', crud='read'):
                yield result
        if view == 'admin.posts_new' \
            and current_user.permission('admin.post', crud='create'):
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
    for result in results:
        view = result[0]
        if view=='admin.countries' \
            and current_user.permission('admin.countries', crud='read'):
                yield result
        if view=='admin.countries_new' \
            and current_user.permission('admin.countries_new', crud='create'):
                yield result


def admin_plugins_sidebar(user):
    results = [
        ('admin.plugins', 'Manage', ''),
    ]
    for result in results:
        view = result[0]
        if view=='admin.plugins' \
            and current_user.permission('admin.plugin', crud='read'):
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
    app.jinja_env.globals.update(admin_event_type_sidebar=admin_event_type_sidebar)
    app.jinja_env.globals.update(admin_post_sidebar=admin_post_sidebar)
    app.jinja_env.globals.update(admin_pages_sidebar=admin_pages_sidebar)
    app.jinja_env.globals.update(admin_emails_sidebar=admin_emails_sidebar)
    app.jinja_env.globals.update(admin_country_sidebar=admin_country_sidebar)
    app.jinja_env.globals.update(admin_plugins_sidebar=admin_plugins_sidebar)
    app.jinja_env.globals.update(admin_settings_sidebar=admin_settings_sidebar)
