from app.admin.utils import get_settings_value
from app.decorators import setup_required
from app.extensions import db
from app.leave.decorators import check_authoriser_access
from app.leave.forms import LeaveForm, LeaveHalfDayForm, LeaveDenyForm
from app.leave.models import Leave, LeaveType
from app.models import EnttLeaveTypes
from app.user.models import User
from sqlalchemy.exc import PendingRollbackError, IntegrityError

import datetime
from flask import render_template, request, url_for, redirect, flash, abort, Blueprint,jsonify, current_app,Response
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import text

leave = Blueprint('leave', __name__, template_folder='templates')

@leave.before_request
@setup_required()
@login_required
def before_request():
    if not current_user.entt:
        return render_template('errors/entt_error.html')
    """
    Protect all post endpoints
    with login_required
    and enabled custom decorator
    """
    pass


def calendar_legend():
    types = []
    types.append('Pending')
    if current_user.check_public_holidays():
        types.append('Public Holiday')
    query = LeaveType.query.filter(LeaveType.active==True).all()
    types += query
    return types


def calendar_settings():
    params = {
        'theme': 'bootstrap',
        'duration_days': 1,
        'weekends': str(current_user.entt.weekend).lower(), #str(current_app.config["ENABLE_WEEKENDS"]).lower(),
        'title_view': 'title',
        'grid_view': 'dayGridMonth,dayGridWeek,dayGridDay',
        'today_view': 'today,prev,next',
        #'initial_view':  'multiMonthYear',
        'initial_view':  'dayGridMonth',
        'display_leave_time': 'false',
        'leave_types': calendar_legend(),
        'pending_colour': get_settings_value('pending_colour'),
        'public_hol_colour': current_user.entt.get_phg_colour()
    }
    return params


def leave_form(obj=None):
    if current_user.entt.half_day:
        return LeaveHalfDayForm(obj=obj)
    else:
        return LeaveForm(obj=obj)


def is_halfday_business_day(date, user):
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
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
    public_holidays = [str(x.start_date.date()) for x in user.check_public_holidays()]
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


def calculate_requested_days(form, leave, user):
    #TODO logic needs sorting
    if hasattr(form, 'half_day'):
        if form.half_day.data == True:
            form.end_date.data = form.start_date.data
            leave.end_date = leave.start_date
            return 0.5
    requested = (form.end_date.data + datetime.timedelta(days=1))
    requested -= form.start_date.data
    if not current_user.entt.weekend:
        result = count_business_days(form.start_date.data,
                                     form.end_date.data,
                                     user)
        return result
    return requested.days


@leave.route('/get-ltype-deductable', methods=['GET', 'POST'])
def get_ltype_deductable():
    id = request.args.get('leave-type-id')
    ltype = EnttLeaveTypes.query.filter(EnttLeaveTypes.leave_type_id==id).first()
    return jsonify({'deduct': f'{ltype.get_deductable()}', 'max_days': f'{ltype.get_max_days()}'})


@leave.route('/calculate-days-async', methods=['GET', 'POST'])
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
        if not current_user.entt.weekend:
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
        if not current_user.entt.weekend:
            result = count_business_days(start_date,
                                         end_date,
                                         current_user)
            return jsonify(f'{result} days')
        return jsonify(f'{requested.days} days')
    # else if no date requested
    return jsonify('')


@leave.route('/calendar', methods=['GET', 'POST'])
def index():
    form = leave_form()
    public_holidays = current_user.check_public_holidays()
    user_leaves = current_user.pending_or_approved_leaves()
    settings = calendar_settings()
    calendar_legend()
    try:
        if form.validate_on_submit():
            leave = Leave()
            form.populate_obj(leave)
            requested = calculate_requested_days(form, leave, current_user)
            #TODO move Error handling to separate function
            #entt_ltype = EnttLeaveTypes.query.filter(EnttLeaveTypes.leave_type_id==form.entt_ltype.data.leave_type_id).first()
            ltype = LeaveType.query.get(form.entt_ltype.data.lt_id)
            if requested > ltype.max_days:
                abort(400, 'Exceeds the maximum length of days you can \
                      request in one occurrence')
            if ltype.deductable:
                if not current_user.days_left:
                    abort(400)
                if requested > current_user.days_left:
                    abort(400, 'Not enough allowance for this request')
            leave.user_id=current_user.id
            leave.ltype_id=ltype.id
            leave.days = requested
            leave.save()
            Leave.initialize_leave_request(leave)
            flash(f'Your request has been submitted', 'success')
            return redirect(url_for('leave.index'))
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    return render_template('personal_calendar.html',
                           form=form,
                           user_leaves=user_leaves,
                           public_holidays=public_holidays,
                           **settings
                           )


@leave.route('/calendar/departments', methods=['GET', 'POST'])
def departments():
    public_holidays = current_user.check_public_holidays()
    settings = calendar_settings()
    form = leave_form()
    return render_template('all_departments_calendar.html',
                           leaves=current_user.all_departments_leaves(),
                           public_holidays=public_holidays,
                           form=form,
                           **settings
                           )


@leave.route('/calendar/departments/<int:id>', methods=['GET', 'POST'])
def department(id):
    public_holidays = current_user.check_public_holidays()
    settings = calendar_settings()
    form = leave_form()
    # avoid circular import
    from app.department.models import Department
    department = Department.query.filter(Department.id==id) \
                                 .filter(Department.active).first_or_404()
    leaves = department.get_member_leaves()
    return render_template('department_calendar.html',
                           department=department,
                           public_holidays=public_holidays,
                           leaves=leaves,
                           form=form,
                           **settings
                           )


@leave.route('/leave/history', defaults={'page': 1}, methods=['GET', 'POST'])
@leave.route('/leave/history/page/<int:page>', methods=['GET', 'POST'])
def history(page):
    form = leave_form()
    leaves = current_user.paginated_leaves(page)
    return render_template('history.html', form=form, leaves=leaves)


@leave.route('/leave/authorise', defaults={'page': 1}, methods=['GET', 'POST'])
@leave.route('/leave/authorise/page/<int:page>', methods=['GET', 'POST'])
@check_authoriser_access()
def authorise(page):
    form = leave_form()
    leaves = current_user.paginated_pending_authoriser_requests(page)
    actioned_leaves = current_user.paginated_actioned_authoriser_requests(page)
    return render_template('pending_requests.html',
                           form=form,
                           leaves=leaves,
                           actioned_leaves=actioned_leaves,
                           )

@leave.route('/leave/authorise/history', defaults={'page': 1}, methods=['GET', 'POST'])
@leave.route('/leave/authorise/history/page/<int:page>', methods=['GET', 'POST'])
@check_authoriser_access()
def authorise_history(page):
    form = leave_form()
    deny_form = LeaveDenyForm()
    actioned_leaves = current_user.paginated_actioned_authoriser_requests(page)
    return render_template('authorise_history.html',
                           form=form,
                           actioned_leaves=actioned_leaves,
                           deny_form=deny_form
                           )


@leave.route('/leave/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    leave = Leave.query.get_or_404(id)
    form = leave_form(obj=leave)
    if current_user != leave.user: #or current_user != leave.user.authoriser:
        abort(403)
    # TODO ONLY Edit Pending Leaves
    if leave.status != 'Pending':
        abort(403)
    if form.validate_on_submit():
        try:
            requested = calculate_requested_days(form, leave, current_user)
            form.populate_obj(leave)
            leave.days = requested
            leave.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            flash('Leave request updated', 'success')
            return redirect(url_for('leave.history'))
    else:
        for error in form.errors.items():
            print(error)
    return render_template('edit_leave.html', leave=leave, form=form)


@leave.route('/leave/<int:id>/delete', methods=['GET', 'POST'])
def delete(id):
    leave = Leave.query.get_or_404(id)
    if current_user != leave.user:
        abort(403)
    if leave.status == 'Pending':
        try:
            leave.delete()
        except Exception as e:
            flash(f'{e}')
        else:
            flash('Leave request deleted', 'success')
    else:
        flash('Cannot delete non-pending requests - contact admin', 'danger')
    return redirect(url_for('leave.index'))


@leave.route('/leave/<int:id>/approve', methods=['GET', 'POST'])
def approve(id):
    """
    Pending leaves to be approved.
    Leave authorisers can only approve.
    If a user's authoriser is changed, pending leave is
    automatically passed over to the authoriser.
    Detect if leave is deductable. If so, allowance will be
    deducted automatically.
    """
    leave = Leave.query.get_or_404(id)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status == 'Approved':
        abort(403) # TODO we don't want leave to be approved again if already approved
    try:
        if leave.ltype.deductable == True:
            if leave.days > leave.user.days_left:
                raise Exception('User does not have enough allowance for this request')
            leave.user.deduct_leave_days(leave.days)
        leave.status = 'Approved'
        leave.actioned_by=current_user
        leave.save()
    except Exception as e:
        flash(f'{e}', 'danger')
    else:
        # celery task
        from app.admin.utils import get_settings_value
        if get_settings_value('system_email_id'):
            from app.email import send_leave_request_status_update_email
            send_leave_request_status_update_email.delay(id)
        flash('Leave request approved', 'success')
    #return redirect(url_for('leave.index'))
    return redirect(url_for('leave.authorise'))


@leave.route('/leave/<int:id>/revoke', methods=['GET', 'POST'])
def revoke(id):
    """
    Only for leaves that have been Approved.
    Only authorisers or those with admin.leave update permissions
    can Revoke.
    Detect if leave_type is deductable. If so, allowance will
    be automatically recalculated.
    Authorisers should only be able to revoke leaves that have
    start_dates no more than 7 days old from the current day.
    ^ For admins 30 days.
    """
    leave = Leave.query.get_or_404(id)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status != 'Approved':
        abort(403)
    form = LeaveDenyForm()
    if form.validate_on_submit():
        try:
            leave.status = 'Revoked'
            leave.status_details = form.status_details.data
            leave.actioned_by=current_user
            if leave.ltype.deductable == True:
                leave.user.reinstate_allowance_days(leave.days)
            leave.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            # celery task
            from app.admin.utils import get_settings_value
            if get_settings_value('system_email_id'):
                from app.email import send_leave_request_status_update_email
                send_leave_request_status_update_email.delay(id)
            flash('Successfully revoked leave request', 'success')
            return redirect(url_for('leave.authorise_history'))
    return render_template('action_request.html', form=form, leave=leave)


@leave.route('/leave/<int:id>/decline', methods=['GET', 'POST'])
def decline(id):
    """
    Only for leaves that are pending.
    Only authorisers can decline.
    Declined Leaves can then be deleted by the user if
    they so wish?
    """
    leave = Leave.query.get_or_404(id)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status != 'Pending':
        abort(403)
    form = LeaveDenyForm()
    if form.validate_on_submit():
        try:
            leave.status = 'Declined'
            leave.status_details = form.status_details.data
            leave.actioned_by=current_user
            leave.save()
        except Exception as e:
            flash(f'{e}', 'danger')
        else:
            # celery task
            from app.admin.utils import get_settings_value
            if get_settings_value('system_email_id'):
                from app.email import send_leave_request_status_update_email
                send_leave_request_status_update_email.delay(id)
            flash('Successfully declined leave request', 'success')
            return redirect(url_for('leave.authorise'))
    return render_template('action_request.html', form=form, leave=leave)
