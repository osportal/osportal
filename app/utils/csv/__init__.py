from app.models import get_class_by_tablename
from app.user.models import User
from app.extensions import db
import csv
from datetime import datetime
from io import BytesIO, StringIO


def dump_table_selected_ids(tablename, ids):
    model = get_class_by_tablename(tablename)

    if model is None:
        raise KeyError("Unknown database table")

    temp = StringIO()
    writer = csv.writer(temp)

    header = model.__mapper__.column_attrs.keys()
    writer.writerow(header)

    query = []

    for id in ids:
        response = model.query.filter(model.id==id)
        for resp in response:
            query.append(resp)

    for curr in query:
        writer.writerow([getattr(curr, column) for column in header])
    temp.seek(0)

    # In Python 3 send_file requires bytes
    output = BytesIO()
    output.write(temp.getvalue().encode("utf-8"))
    output.seek(0)
    temp.close()

    return output


def dump_database_table(tablename):
    # TODO: It might make sense to limit dumpable tables. Config could potentially leak sensitive information.
    model = get_class_by_tablename(tablename)

    if model is None:
        raise KeyError("Unknown database table")

    temp = StringIO()
    writer = csv.writer(temp)

    header = model.__mapper__.column_attrs.keys()
    writer.writerow(header)

    responses = model.query.all()

    for curr in responses:
        writer.writerow([getattr(curr, column) for column in header])

    temp.seek(0)

    # In Python 3 send_file requires bytes
    output = BytesIO()
    output.write(temp.getvalue().encode("utf-8"))
    output.seek(0)
    temp.close()

    return output


def dump_users_with_fields_csv():
    temp = StringIO()
    writer = csv.writer(temp)

    user_fields = User.query.all()
    user_field_ids = [f.id for f in user_fields]
    user_field_names = [f.username for f in user_fields]

    header = [column.name for column in User.__mapper__.columns] + user_field_names
    writer.writerow(header)

    responses = User.query.all()

    for curr in responses:
        user_field_entries = {f.field_id: f.value for f in curr.field_entries}
        user_field_values = [
            user_field_entries.get(f_id, "") for f_id in user_field_ids
        ]
        user_row = [
            getattr(curr, column.name) for column in User.__mapper__.columns
        ] + user_field_values
        writer.writerow(user_row)

    temp.seek(0)

    # In Python 3 send_file requires bytes
    output = BytesIO()
    output.write(temp.getvalue().encode("utf-8"))
    output.seek(0)
    temp.close()

    return output

def dump_csv(name):
    #dump_func = CSV_KEYS.get(name)
    #if dump_func:
    if get_class_by_tablename(name):
        return dump_database_table(tablename=name)
    else:
        raise KeyError



def load_csv(cls, dict_reader):
    date_time_format = '%Y-%m-%d %H:%M:%S.%f'
    date_format = '%Y-%m-%d %H:%M:%S'
    date_time_columns = ['created_at','updated_at', 'last_notification_read_time','last_login_time', 'current_login_time']
    date_only_columns = ['start_date', 'leave_year_start']
    errors = []
    new_line = {}
    for i, line in enumerate(dict_reader):
        try:
            for k, v in line.items():
                if v.lower() == 'true':
                    line[k]=True
                elif v.lower() == 'false':
                    line[k]=False
                # if theres no data for a column do not add to new dict
                if line[k] != '' or None:
                    new_line[k] = line[k]
                # if its a datetime column and not blank
                # then convert str to timeformat
                if k in date_time_columns:
                    if line[k] != '' or None:
                        new_line[k] = datetime.strptime(line[k], date_time_format)
                if k in date_only_columns:
                    if line[k] != '' or None:
                        new_line[k] = datetime.strptime(line[k], date_format)
            # print new key,value in new dict for testing
            '''
            for k, v in new_line.items():
                print(k)
                print(v)
            '''
            obj = cls(**{str(k): v for k, v in new_line.items() if type(k) != bool})
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            exception = f'Line {i+1}: {e.__class__.__name__}: {e}'
            errors.append(exception)
    if errors:
        return errors
    return True
