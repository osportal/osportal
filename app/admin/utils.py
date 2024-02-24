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
