import dataset
import datetime
import json
import os
import re
import subprocess  # nosec B404
import sys
import tempfile
import zipfile

from alembic.migration import MigrationContext
from app.extensions import db
from app.models import get_class_by_tablename
from app.utils.zip.freeze import freeze_export
from flask import current_app
from flask_migrate import upgrade as migration_upgrade
from io import BytesIO
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.sql import sqltypes, text



def get_current_revision():
    #engine = create_engine(app.config.get("SQLALCHEMY_DATABASE_URI"))
    engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])
    conn = engine.connect()
    #conn = db.engine.connect()
    context = MigrationContext.configure(conn)
    current_rev = context.get_current_revision()
    return current_rev


def export_zipfile():
    # TODO: For some unknown reason dataset is only able to see alembic_version during tests.
    # Even using a real sqlite database. This makes this test impossible to pass in sqlite.
    db = dataset.connect(current_app.config["SQLALCHEMY_DATABASE_URI"])

    # Backup database
    backup = tempfile.NamedTemporaryFile()

    backup_zip = zipfile.ZipFile(backup, "w")

    tables = db.tables
    for table in tables:
        result = db[table].all()
        #table_obj = db.Table(table,db.metadata)# db.metadata, autoload=True, autoload_with=db.engine)
        #query = db.select([table_obj])
        #execute = db.engine.execute(query)
        #result = execute.fetchall()
        result_file = BytesIO()
        freeze_export(result, fileobj=result_file)
        result_file.seek(0)
        backup_zip.writestr("db/{}.json".format(table), result_file.read())

    # # Guarantee that alembic_version is saved into the export
    if "alembic_version" not in tables:
        result = {
            "count": 1,
            "results": [{"version_num": get_current_revision()}],
            "meta": {}
        }
        result_file = BytesIO()
        #json.dump(result, result_file)
        freeze_export(result, fileobj=result_file)
        result_file.seek(0)
        backup_zip.writestr("db/alembic_version.json", result_file.read())

    # Backup uploads
    '''
    uploader = get_uploader()
    uploader.sync()

    upload_folder = os.path.join(
        os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
    )
    for root, _dirs, files in os.walk(upload_folder):
        for file in files:
            parent_dir = os.path.basename(root)
            backup_zip.write(
                os.path.join(root, file),
                arcname=os.path.join("uploads", parent_dir, file),
            )
    '''

    backup_zip.close()
    backup.seek(0)
    db.close()
    return backup


def import_zipfile(backup, erase=True):
    backup = zipfile.ZipFile(backup)
    members = backup.namelist()
    member_dirs = [os.path.split(m)[0] for m in members if "/" in m]
    if "db" not in member_dirs:
        raise Exception('''
        Could not find the db folder in this backup,
        therefore the import process cannot continue
                        ''')
    ''' temporarily remove need for alembic_version
    try:
        alembic_version = json.loads(backup.open("db/alembic_version.json").read())
        alembic_version = alembic_version["results"][0]["version_num"]
    except Exception:
        raise Exception("""
            Could not determine appropriate database version.
            This backup cannot be automatically imported.
                        """)
    '''
    postgres = current_app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres")
    mysql = current_app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql")
    side_db = dataset.connect(current_app.config["SQLALCHEMY_DATABASE_URI"])
    first = [
        "db/page.json",
        "db/leave_type.json",
        "db/country.json",
        "db/public_holiday.json",
        "db/settings.json",
        "db/role.json",
        "db/user.json",
        "db/department.json",
        "db/department_members.json",
        "db/notification.json",
        "db/post.json",
        "db/comment.json",
        "db/leave.json",
        "db/leave_actioned.json",
    ]
    # Upgrade the database to the point in time that the import was taken from
    #migration_upgrade(revision=alembic_version)
    def insertion(table_filenames):
        for member in table_filenames:
            print(f"inserting {member}...")
            if member.startswith("db/"):
                table_name = member[3:-5]
                # Try to open a file but skip if it doesn't exist.
                try:
                    data = backup.open(member).read()
                except KeyError:
                    continue

                if data:
                    table = side_db[table_name]

                    saved = json.loads(data)
                    count = len(saved["results"])
                    for i, entry in enumerate(saved["results"]):
                        print(f"inserting {member} {i}/{count}")
                        try:
                            table.insert(entry)
                        # if unique constraint violation, skip
                        except (ProgrammingError,IntegrityError):
                            pass
                        db.session.commit()
                    if postgres:
                        # This command is to set the next primary key ID for the re-inserted tables in Postgres. However,
                        # this command is very difficult to translate into SQLAlchemy code. Because Postgres is not
                        # officially supported, no major work will go into this functionality.
                        # https://stackoverflow.com/a/37972960
                        if '"' not in table_name and "'" not in table_name:
                            query = "SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), coalesce(max(id)+1,1), false) FROM \"{table_name}\"".format(  # nosec
                                table_name=table_name
                            )
                            side_db.engine.execute(query)
                        else:
                            raise Exception(
                                f"Exception: Table name {table_name} contains quotes"
                            )
    insertion(first)
    # Alembic sqlite support is lacking so we should just create_all anyway
    print("running head migrations")
    # Run migrations to bring to latest version
    migration_upgrade(revision="head")
    # Create any leftover tables, perhaps from old plugins
    db.create_all()
    try:
        print("reenabling foreign key checks")
        if postgres:
            side_db.query("SET session_replication_role=DEFAULT;")
        else:
            side_db.query("SET FOREIGN_KEY_CHECKS=1;")
    except Exception:
        print("Failed to enable foreign key checks. Continuing.")



def set_import_error(value, timeout=604800, skip_print=False):
    cache.set(key="import_error", value=value, timeout=timeout)
    if not skip_print:
        print(value)


def set_import_status(value, timeout=604800, skip_print=False):
    cache.set(key="import_status", value=value, timeout=timeout)
    if not skip_print:
        print(value)

def set_import_start_time(value, timeout=604800, skip_print=False):
    cache.set(key="import_start_time", value=value, timeout=timeout)
    if not skip_print:
        print(value)


def set_import_end_time(value, timeout=604800, skip_print=False):
    cache.set(key="import_end_time", value=value, timeout=timeout)
    if not skip_print:
        print(value)
