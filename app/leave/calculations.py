import datetime
from flask_login import current_user
from flask import abort


#TODO check if weekend_days are enabled
# then check is_deductable? for either halfday_business_day or count_business_day function
# requested days should return 0 only if is_deductable else it should return days

def is_halfday_business_day(date, user):
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
    # Define a list of weekend days (Saturday and Sunday)
    # Monday is 0 and Sunday is 6
    weekend_days = [5, 6]
    current_date = date

    # Determine half-day value based on time unit
    # if working_hours_per_day has no value it will default to 8 (therefore half day value is 4)
    if user.entt.time_unit == "days":
        half_day_value = 0.5
    else:
        half_day_value = (user.entt.working_hours_per_day / 2) if user.entt.working_hours_per_day else 4


    # Check if the current day is a weekend day
    if not user.entt.weekend:
        if current_date.weekday() not in weekend_days and str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
            return half_day_value
        return 0
    else:
        if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
            return half_day_value
        return 0


def count_business_days(start_date, end_date, user):
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
    # Define a list of weekend days (Saturday and Sunday)
    weekend_days = [5, 6]  # Monday is 0 and Sunday is 6
    # Initialize a counter for business days
    business_days = 0
    business_hours = 0

    # Determine full-day working hours
    working_hours_per_day = user.entt.working_hours_per_day if user.entt.working_hours_per_day else 8

    # Iterate through each day in the date range
    current_date = start_date
    while current_date <= end_date:
        # Check if the current day is a business day
        is_weekend = current_date.weekday() in weekend_days
        is_public_holiday = str(current_date.strftime('%Y-%m-%d')) in public_holidays

        if not user.entt.weekend:
            if not is_weekend and not is_public_holiday:
                if user.entt.time_unit == "days":
                    business_days += 1
                elif user.entt.time_unit == "hours":
                    business_hours += working_hours_per_day
        else:
            if not is_public_holiday:
                if user.entt.time_unit == "days":
                    business_days += 1
                elif user.entt.time_unit == "hours":
                    business_hours += working_hours_per_day
        # Move to the next day
        current_date += datetime.timedelta(days=1)
    return business_days if user.entt.time_unit == "days" else business_hours


def calculate_requested_days(start_date, end_date, user, half_day=None):
    if half_day:
        return is_halfday_business_day(start_date, user)
    result = count_business_days(start_date, end_date, user)
    return result


def validate_request(ltype, requested, user):
    if not requested > 0:
        raise Exception('No working days were requested')

    if ltype.deductable:
        if user.entitlement_rem is None:
            raise Exception('Entitlement Remaining is NULL. Please contact your administrator')
        if user.entt.time_unit == "days" and requested > user.entitlement_rem:
            raise Exception('You do not have sufficient allowance for this request')
        elif user.entt.time_unit == "hours" and requested > user.entitlement_rem:
            raise Exception('You do not have sufficient allowance for this request')
    return True
