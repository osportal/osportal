import datetime
from flask_login import current_user
from flask import abort


#TODO check if weekend_days are enabled
# then check is_deductable? for either halfday_business_day or count_business_day function
# requested days should return 0 only if is_deductable else it should return days

def is_halfday_business_day(date, user):
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
    # Define a list of weekend days (Saturday and Sunday)
    weekend_days = [5, 6]  # Monday is 0 and Sunday is 6
    # Iterate through each day in the date range
    current_date = date
    # Check if the current day is a weekend day
    if not user.entt.weekend:
        if current_date.weekday() not in weekend_days:
            if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
                return 0.5
        return 0
    else:
        if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
            return 0.5
        return 0


def count_business_days(start_date, end_date, user):
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
    # Define a list of weekend days (Saturday and Sunday)
    weekend_days = [5, 6]  # Monday is 0 and Sunday is 6
    # Initialize a counter for business days
    business_days = 0
    # Iterate through each day in the date range
    current_date = start_date
    while current_date <= end_date:
        # Check if the current day is a weekend day
        if not user.entt.weekend:
            if current_date.weekday() not in weekend_days:
                if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
                    business_days += 1
        else:
            if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
                business_days += 1
        # Move to the next day
        current_date += datetime.timedelta(days=1)
    return business_days


def calculate_requested_days(start_date, end_date, user, half_day=None):
    if half_day:
        return is_halfday_business_day(start_date, user)
    result = count_business_days(start_date, end_date, user)
    return result


def validate_request(ltype, requested, user):
    if not requested > 0:
        raise Exception('No working days were requested')
    if ltype.deductable:
        if requested > user.days_left:
            raise Exception('You do not have sufficient allowance for this request')
    return True
