from wtforms.validators import ValidationError
from app.department.models import Department
from sqlalchemy import func

def check_dept_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    dept = Department.query.filter(func.lower(Department.name)==field.data.lower()).first()
    if dept:
        raise ValidationError('Department already exists')
