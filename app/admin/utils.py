from flask import current_app

def prefix_name(obj, file_data):
    parts = os.path.splitext(file_data.filename)
    return secure_filename('file-%s%s' % parts)


def user_admin_upload(form_picture):
    random_hex = secrets.token_hex(8)
    print(random_hex)
    print(form_picture)
    return random_hex
    """
    _, f_ext = os.path.splitext(form_picture)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.static_folder+'/profile_pics',
                                picture_fn)
    output_size = (256, 256)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn
"""

def get_settings_value(attr):
    from app.admin.models import Settings
    settings = Settings.query.first_or_404()
    return getattr(settings, attr)


def check_licence(increment=0):
    max_users = current_app.config['MAX_ACTIVE_USERS']
    if not max_users:
        # no licence restriction, allow unlimited users
        return
    from app.admin.models import Dashboard
    active_users = Dashboard.group_and_count_active_users()
    current_total = active_users['total']
    if current_total + increment > max_users:
        raise Exception(
            f'You do not have enough user licenses. Allowed: {max_users}, Current: {current_total}, Attempted: {current_total + increment}'
        )
