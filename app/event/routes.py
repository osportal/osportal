from app.admin.utils import get_settings_value
from app.decorators import setup_required
from app.extensions import db
from app.event.decorators import check_authoriser_access
from app.event.forms import EventForm, EventHalfDayForm, EventDenyForm
from app.event.models import Event, EventType
from app.user.models import User

import datetime
from flask import render_template, request, url_for, redirect, flash, abort, Blueprint,jsonify, current_app,Response
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import text

event = Blueprint('event', __name__, template_folder='templates')

@event.before_request
@setup_required()
@login_required
def before_request():
    if current_user.country == None:
        return render_template('errors/auth_country_error.html')
    """
    Protect all post endpoints
    with login_required
    and enabled custom decorator
    """
    pass


def calendar_legend():
    types = ['Pending', 'Public Holiday']
    query = EventType.query.filter(EventType.active==True).all()
    types += query
    return types


def calendar_settings():
    params = {
        'theme': 'bootstrap',
        'duration_days': 1,
        'weekends': str(get_settings_value('weekend')).lower(), #str(current_app.config["ENABLE_WEEKENDS"]).lower(),
        'left_view': 'dayGridMonth,dayGridWeek,dayGridDay',
        'center_view': 'title',
        #'initial_view':  'multiMonthYear',
        'initial_view':  'dayGridMonth',
        'display_event_time': 'false',
        'event_types': calendar_legend(),
        'pending_colour': get_settings_value('pending_colour'),
        'public_hol_colour': get_settings_value('public_holiday_colour')
    }
    return params


def event_form(obj=None):
    if get_settings_value('half_day'):
        return EventHalfDayForm(obj=obj)
    else:
        return EventForm(obj=obj)


def is_halfday_business_day(date, user):
    public_holidays = [str(x.start_date.date()) for x in user.country.holidays]
    # Define a list of weekend days (Saturday and Sunday)
    weekend_days = [5, 6]  # Monday is 0 and Sunday is 6
    # Initialize a counter for business days
    business_days = 0
    # Iterate through each day in the date range
    current_date = date
    # Check if the current day is a weekend day
    if current_date.weekday() not in weekend_days:
        if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
            return '0.5';
    return '0';


def count_business_days(start_date, end_date, user):
    public_holidays = [str(x.start_date.date()) for x in user.country.holidays]
    # Define a list of weekend days (Saturday and Sunday)
    weekend_days = [5, 6]  # Monday is 0 and Sunday is 6
    # Initialize a counter for business days
    business_days = 0
    # Iterate through each day in the date range
    current_date = start_date
    while current_date <= end_date:
        # Check if the current day is a weekend day
        if current_date.weekday() not in weekend_days:
            if str(current_date.strftime('%Y-%m-%d')) not in public_holidays:
                business_days += 1
        # Move to the next day
        current_date += datetime.timedelta(days=1)
    return business_days


def calculate_requested_days(form, event, user):
    #TODO logic needs sorting
    if hasattr(form, 'half_day'):
        if form.half_day.data == True:
            form.end_date.data = form.start_date.data
            event.end_date = event.start_date
            return 0.5
    requested = (form.end_date.data + datetime.timedelta(days=1))
    requested -= form.start_date.data
    if not get_settings_value('weekend'):
        result = count_business_days(form.start_date.data,
                                     form.end_date.data,
                                     user)
        return result
    return requested.days


@event.route('/get-etype-deductable', methods=['GET', 'POST'])
def get_etype_deductable():
    id = request.args.get('event-type-id')
    etype = EventType.query.get(id)
    return jsonify({'deduct': f'{etype.deductable}', 'max_days': f'{etype.max_days}'})


@event.route('/calculate-days-async', methods=['GET', 'POST'])
def calculate_days_async():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    half_day = request.args.get('half_day')
    date_format = '%Y-%m-%d'
    if start_date and half_day:
        try:
            start_date = datetime.datetime.strptime(start_date, date_format)
        except Exception as e:
             return jsonify(
                message=("Invalid date format"),
                data=None,
                status=400
            )
        if not get_settings_value('weekend'):
             result = is_halfday_business_day(start_date, current_user)
             if result:
                 return jsonify(f'{result} days')
    # convert javascript string to datetime object
    if start_date and end_date:
        try:
            start_date = datetime.datetime.strptime(start_date, date_format)
            end_date = datetime.datetime.strptime(end_date, date_format)
        except Exception as e:
             return jsonify(
                message=("Invalid date format"),
                data=None,
                status=400
            )
            #return make_response(jsonify(f'{e}'), 400)

        requested = (end_date + datetime.timedelta(days=1))
        requested -= start_date
        if not get_settings_value('weekend'):
            result = count_business_days(start_date,
                                         end_date,
                                         current_user)
            return jsonify(f'{result} days')
        return jsonify(f'{requested.days} days')
    # else if no date requested
    return jsonify('')


@event.route('/calendar', methods=['GET', 'POST'])
def index():
    form = event_form()
    ##TODO redo this horrible shit
    if current_user.entt:
        public_holidays = current_user.entt.public_holiday_group.holidays
    else:
        public_holidays = []
    ##
    user_events = current_user.pending_or_approved_events()
    settings = calendar_settings()
    calendar_legend()
    try:
        if form.validate_on_submit():
            event = Event()
            requested = calculate_requested_days(form, event, current_user)
            #TODO move Error handling to separate function
            etype = EventType.query.get(form.etype.data.id)
            if requested > etype.max_days:
                abort(400, 'Exceeds the maximum length of days you can \
                      request in one occurrence')
            if etype.deductable:
                if not current_user.days_left:
                    abort(400)
                if requested > current_user.days_left:
                    abort(400, 'Not enough allowance for this request')
            form.populate_obj(event)
            event.user_id=current_user.id
            event.etype_id=form.etype.data.id
            event.days = requested
            event.save()
            Event.initialize_event_request(event)
            flash(f'Your request has been submitted', 'success')
            return redirect(url_for('event.index'))
    except Exception as e:
        flash(f'{e}', 'danger')
    return render_template('personal_calendar.html',
                           form=form,
                           user_events=user_events,
                           public_holidays=public_holidays,
                           **settings
                           )


@event.route('/calendar/departments', methods=['GET', 'POST'])
def departments():
    public_holidays = current_user.country.holidays
    settings = calendar_settings()
    form = event_form()
    return render_template('all_departments_calendar.html',
                           events=current_user.all_departments_events(),
                           public_holidays=public_holidays,
                           form=form,
                           **settings
                           )


@event.route('/calendar/departments/<int:id>', methods=['GET', 'POST'])
def department(id):
    public_holidays = current_user.country.holidays
    settings = calendar_settings()
    form = event_form()
    # avoid circular import
    from app.department.models import Department
    department = Department.query.filter(Department.id==id) \
                                 .filter(Department.active).first_or_404()
    events = department.get_member_events()
    return render_template('department_calendar.html',
                           department=department,
                           public_holidays=public_holidays,
                           events=events,
                           form=form,
                           **settings
                           )


@event.route('/event/history', defaults={'page': 1}, methods=['GET', 'POST'])
@event.route('/event/history/page/<int:page>', methods=['GET', 'POST'])
def history(page):
    form = event_form()
    events = current_user.paginated_events(page)
    return render_template('history.html', form=form, events=events)


@event.route('/event/authorise', defaults={'page': 1}, methods=['GET', 'POST'])
@event.route('/event/authorise/page/<int:page>', methods=['GET', 'POST'])
@check_authoriser_access()
def authorise(page):
    form = event_form()
    events = current_user.paginated_pending_authoriser_requests(page)
    actioned_events = current_user.paginated_actioned_authoriser_requests(page)
    return render_template('pending_requests.html',
                           form=form,
                           events=events,
                           actioned_events=actioned_events,
                           )

@event.route('/event/authorise/history', defaults={'page': 1}, methods=['GET', 'POST'])
@event.route('/event/authorise/history/page/<int:page>', methods=['GET', 'POST'])
@check_authoriser_access()
def authorise_history(page):
    form = event_form()
    deny_form = EventDenyForm()
    actioned_events = current_user.paginated_actioned_authoriser_requests(page)
    return render_template('authorise_history.html',
                           form=form,
                           actioned_events=actioned_events,
                           deny_form=deny_form
                           )


@event.route('/event/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    event = Event.query.get_or_404(id)
    form = event_form(obj=event)
    if current_user != event.user: #or current_user != event.user.authoriser:
        abort(403)
    # TODO ONLY Edit Pending Events
    if event.status != 'Pending':
        abort(403)
    if form.validate_on_submit():
        try:
            requested = calculate_requested_days(form, event, current_user)
            form.populate_obj(event)
            event.days = requested
            event.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Event request updated', 'success')
            return redirect(url_for('event.history'))
    else:
        for error in form.errors.items():
            print(error)
    return render_template('edit_event.html', event=event, form=form)


@event.route('/event/<int:id>/delete', methods=['GET', 'POST'])
def delete(id):
    event = Event.query.get_or_404(id)
    if current_user != event.user:
        abort(403)
    if event.status == 'Pending':
        try:
            event.delete()
        except Exception as e:
            flash(f'{e}')
        else:
            flash('Event request deleted', 'success')
    else:
        flash('Cannot delete non-pending requests - contact admin', 'danger')
    return redirect(url_for('event.index'))


@event.route('/event/<int:id>/approve', methods=['GET', 'POST'])
def approve(id):
    """
    Pending events to be approved.
    Leave authorisers can only approve.
    If a user's authoriser is changed, pending event is
    automatically passed over to the authoriser.
    Detect if event is deductable. If so, allowance will be
    deducted automatically.
    """
    event = Event.query.get_or_404(id)
    if current_user != event.user.authoriser:
        abort(403)
    if event.status == 'Approved':
        abort(403) # TODO we don't want event to be approved again if already approved
    try:
        if event.etype.deductable == True:
            if event.days > event.user.days_left:
                raise Exception('User does not have enough allowance for this request')
            event.user.deduct_leave_days(event.days)
        event.status = 'Approved'
        event.actioned_by=current_user
        event.save()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        # celery task
        from app.email import send_event_request_status_update_email
        send_event_request_status_update_email.delay(id)
        flash('Event request approved', 'success')
    #return redirect(url_for('event.index'))
    return redirect(url_for('event.authorise'))


@event.route('/event/<int:id>/revoke', methods=['GET', 'POST'])
def revoke(id):
    """
    Only for events that have been Approved.
    Only authorisers or those with admin.event update permissions
    can Revoke.
    Detect if event_type is deductable. If so, allowance will
    be automatically recalculated.
    Authorisers should only be able to revoke events that have
    start_dates no more than 7 days old from the current day.
    ^ For admins 30 days.
    """
    event = Event.query.get_or_404(id)
    if current_user != event.user.authoriser:
        abort(403)
    if event.status != 'Approved':
        abort(403)
    form = EventDenyForm()
    if form.validate_on_submit():
        try:
            event.status = 'Revoked'
            event.status_details = form.status_details.data
            event.actioned_by=current_user
            if event.etype.deductable == True:
                event.user.reinstate_allowance_days(event.days)
            event.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            # celery task
            from app.email import send_event_request_status_update_email
            send_event_request_status_update_email.delay(id)
            flash('Successfully revoked event request', 'success')
            return redirect(url_for('event.authorise_history'))
    return render_template('action_request.html', form=form, event=event)


@event.route('/event/<int:id>/decline', methods=['GET', 'POST'])
def decline(id):
    """
    Only for events that are pending.
    Only authorisers can decline.
    Declined Events can then be deleted by the user if
    they so wish?
    """
    event = Event.query.get_or_404(id)
    if current_user != event.user.authoriser:
        abort(403)
    if event.status != 'Pending':
        abort(403)
    form = EventDenyForm()
    if form.validate_on_submit():
        try:
            event.status = 'Declined'
            event.status_details = form.status_details.data
            event.actioned_by=current_user
            event.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            # celery task
            from app.email import send_event_request_status_update_email
            send_event_request_status_update_email.delay(id)
            flash('Successfully declined event request', 'success')
            return redirect(url_for('event.authorise'))
    return render_template('action_request.html', form=form, event=event)
