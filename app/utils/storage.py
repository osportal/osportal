from flask import current_app
import os

def upload_folder():
    if current_app.config['UPLOAD_STORAGE_PATH']:
        return current_app.config['UPLOAD_STORAGE_PATH']
    else:
        return os.path.join(current_app.root_path, 'uploads')
