from PIL import Image
from datetime import datetime
from flask import current_app
import os
import secrets


def delete_picture(form_picture):
    # if image_file exists in user obj, not the default None
    if form_picture is not None:
        picture_path = os.path.join(current_app.root_path,
                                    current_app.static_folder+'/img/profile_pics',
                                    form_picture)
        # if there is an image_file string attached to user
        # make sure image_file we are about to delete exists
        # if not pass - return None, otherwise delete
        if not os.path.exists(picture_path):
            return None
        return os.remove(picture_path)


def save_picture(form_picture):
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path,
                                current_app.static_folder+'/img/profile_pics',
                                picture_fn)
    output_size = (256, 256)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn