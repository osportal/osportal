from PIL import Image, UnidentifiedImageError
from app.utils.storage import upload_folder
from datetime import datetime
from flask import current_app
import os
from pathlib import Path
import secrets


def is_valid_image_pillow(file_name):
    try:
        with Image.open(file_name) as img:
            img.verify()
    except (IOError, SyntaxError, UnidentifiedImageError):
        return False
    else:
        return True


def delete_picture(form_picture):
    # if image_file exists in user obj, not the default None
    if form_picture:
        picture_path = os.path.join(upload_folder(), 'profile',
                                    form_picture)
        # if there is an image_file string attached to user
        # make sure image_file we are about to delete exists
        # if not pass - return None, otherwise delete
        if not os.path.exists(picture_path):
            return None
        return os.remove(picture_path)


def save_picture(form_picture):
    #is_valid_image_pillow(form_picture)
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    path = Path(upload_folder(), 'profile')
    path.mkdir(parents=True, exist_ok=True)
    output_size = (400, 400)
    image = Image.open(form_picture)
    image.thumbnail(output_size, Image.Resampling.LANCZOS)
    image.save(os.path.join(path, picture_fn), quality=100)

    return picture_fn
