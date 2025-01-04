from app.leave.models import LeaveType
from app.leave.calculations import (count_business_days,
                                    calculate_requested_days,
                                    )
from app.models import EnttLeaveTypes
import datetime
from flask_login import current_user
from sqlalchemy import func
from wtforms_components import DateRange
from wtforms.validators import ValidationError, StopValidation, DataRequired


# leave type validation
def check_lt_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    lt = LeaveType.query.filter(func.lower(LeaveType.name)==field.data.lower()).first()
    if lt:
        raise ValidationError('Leave Type already exists')


def check_approval(form, field):
    """
    if selected leave type requires approval
    make sure user has an authoriser """
    ltype = EnttLeaveTypes.query.filter(EnttLeaveTypes.leave_type_id==form.entt_ltype.data.leave_type_id).first()
    if ltype.get_approval():
        if not current_user.authoriser:
            raise ValidationError('''This Type requires an authoriser to be
                                  assigned to your profile. Contact administrator.''')


def check_end_date(form, field):
    if hasattr(form, 'half_day'):
        if form.half_day.data == True:
            raise StopValidation()
    if field.data != None:
        if field.data < form.start_date.data:
            raise ValidationError('End Date cannot be earlier than the start date')
    ltype = EnttLeaveTypes.query.filter(EnttLeaveTypes.leave_type_id==form.entt_ltype.data.leave_type_id).first()
    if ltype.get_deductable():
        # this will only apply to deductable i.e leave requests
        from flask_login import current_user
        if current_user.leave_year_start:
            #replace leave_year_start with current year
            #then add 1 year onto for max end_date
            max_end_year = current_user.leave_year_start.replace(year=datetime.datetime.today().year+1)
            if form.end_date.data > max_end_year:
                raise ValidationError(f'End date must be before your next leave year start ({max_end_year})')
            DataRequired()


def check_leave_year_start(form, field):
    from flask_login import current_user
    if not current_user.leave_year_start: #if leave_year_start is None
        raise ValidationError('You must have a leave year start date. Contact administrator.')
    else:
        # get only day and month from leave_year_start
        current_leave_year = current_user.leave_year_start.replace(year=datetime.datetime.today().year)
        # year has to be replaced with current_year
        if current_leave_year > form.start_date.data:
            raise ValidationError(f'Start date must be greater than current leave year {current_leave_year}')


#TODO below has been commented out from leave/forms
# below validator does not take into account public holidays / weekends
def check_allowance(form, field):
    # check available allowance if leave type is deductable
    ltype = EnttLeaveTypes.query.filter(EnttLeaveTypes.leave_type_id==form.entt_ltype.data.leave_type_id).first()
    if ltype.get_deductable():
        from flask_login import current_user
        if hasattr(form, 'half_day'):
            if form.half_day.data == True:
                requested = calculate_requested_days(form.start_date.data, form.end_date.data, current_user, half_day=True)
        requested = calculate_requested_days(form.start_date.data, form.end_date.data, current_user)
        if requested > current_user.entitlement_rem:
                raise ValidationError(f'You do not have sufficient leave allowance for requested days.')
