from app.admin.utils import get_settings_value
from app.admin.forms import SearchForm
from app.decorators import setup_required
from app.extensions import db
from app.leave.calculations import (is_halfday_business_day,
                                    count_business_days,
                                    calculate_requested_days,
                                    validate_request)
from app.leave.decorators import check_authoriser_access
from app.leave.forms import LeaveForm, LeaveHalfDayForm, LeaveDenyForm
from app.leave.models import Leave, LeaveType, LeaveActioned
from app.models import EnttLeaveTypes
from app.user.models import User
from sqlalchemy.exc import PendingRollbackError, IntegrityError

import datetime
from flask import (render_template, request, url_for, redirect, flash, abort,
                   Blueprint,jsonify, current_app, Response)
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import text

leave = Blueprint('leave', __name__, template_folder='./templates')

@leave.before_request
@setup_required()
@login_required
def before_request():
    if not current_user.entt:
        return render_template('errors/entt_error.html')
    """
    Protect all leave endpoints
    with login_required
    and enabled custom decorator
    """
    pass


def calendar_settings():
    params = {
        'theme': 'bootstrap',
        'duration_days': 1,
        'weekends': str(current_user.get_entt_weekend()).lower(),
        'title_view': 'title',
        'grid_view': 'dayGridMonth,dayGridWeek,dayGridDay',
        'today_view': 'today,prev,next',
        #'initial_view':  'multiMonthYear',
        'initial_view':  'dayGridMonth',
        'display_leave_time': 'false',
    }
    return params


def leave_form(obj=None):
    if current_user.entt.half_day:
        return LeaveHalfDayForm(obj=obj)
    else:
        return LeaveForm(obj=obj)


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
    public_holidays = current_user.check_public_holidays()
    user_leaves = current_user.pending_or_approved_leaves()
    settings = calendar_settings()
    return render_template('personal_calendar.html',
                           public_holidays=public_holidays,
                           user_leaves=user_leaves,
                           user=current_user,
                           **settings
                           )


@leave.route('/leave/<int:id>', methods=['GET', 'POST'])
@leave.route('/leave/create', methods=['GET', 'POST'], defaults={'id': None})
def manage(id):
    leave = Leave.query.get_or_404(id) if id else Leave()
    form = leave_form(obj=leave)
      # Ensure the current user is authorized to edit the leave
    if id:
        if current_user != leave.user:
            abort(403)
        # Only allow editing Pending leave requests
        if leave.status != 'Pending':
            abort(403)

    try:
        if form.validate_on_submit():
            # calculate if half days
            if form.half_day.data:
                requested = calculate_requested_days(form.start_date.data,
                                                     form.end_date.data,
                                                     current_user,
                                                     half_day=True)
            else:
                # otherwise calculate normal days
                requested = calculate_requested_days(form.start_date.data,
                                                     form.end_date.data,
                                                     current_user)
            ltype = LeaveType.query.get(form.entt_ltype.data.lt_id)
            if validate_request(ltype, requested, current_user):
                form.populate_obj(leave)
                leave.user_id=current_user.id
                leave.ltype_id=ltype.id
                # use function to detect entt days / hours and convert accordingly
                leave.duration = requested
                leave.time_unit = current_user.entt.time_unit

                # if new booking, save
                if not id:
                    leave.save()
                    leave.init_request()
                    flash('Your leave request has been submitted', 'success')
                else:
                    leave.save()
                    flash('Leave request updated', 'success')
                return redirect(url_for('leave.history' if id else 'leave.index'))
    except (IntegrityError, PendingRollbackError) as e:
        db.session.rollback()
        flash(f'{e.orig.diag.message_detail}', 'danger')
    except Exception as e:
        flash(f'{e}', 'danger')
    return render_template('edit_leave.html', form=form, leave=leave)


@leave.route('/calendar/departments', methods=['GET', 'POST'])
def departments():
    public_holidays = current_user.check_public_holidays()
    settings = calendar_settings()
    form = leave_form()
    return render_template('all_departments_calendar.html',
                           leaves=current_user.all_departments_leaves(),
                           public_holidays=public_holidays,
                           form=form,
                           user=current_user,
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
                           user=current_user,
                           **settings
                           )


@leave.route('/leave/history/user/<int:page_param_first>', defaults={'page_param_second': 1, 'page_param_third': 1}, methods=['GET', 'POST'])
@leave.route('/leave/history/user/<int:page_param_first>/leave_page/<int:page_param_second>/holiday_page/<int:page_param_third>', methods=['GET', 'POST'])
def history(page_param_first, page_param_second, page_param_third ):
    user = User.query.get_or_404(page_param_first)
    heading = None
    if current_user != user:
        if current_user != user.authoriser:
            abort(403)
        else:
            heading = f'{user} Records'
    form = leave_form()
    leaves = user.paginated_leaves(page_param_second)
    paginated_holidays=None
    if user.entt:
        paginated_holidays = user.entt.paginated_holidays(page_param_third)
    return render_template('history.html',
                           form=form,
                           leaves=leaves,
                           user=user,
                           heading=heading,
                           paginated_holidays=paginated_holidays,
                           page_param_first=page_param_first,
                           page_param_second=page_param_second,
                           page_param_third=page_param_third
                           )


@leave.route('/leave/authorise', defaults={'page_param_first': 1, 'page_param_second': 1, 'page_param_third': 1}, methods=['GET', 'POST'])
@leave.route('/leave/authorise/pending/<int:page_param_first>/actioned/<int:page_param_second>/users/<int:page_param_third>', methods=['GET', 'POST'])
@check_authoriser_access()
def authorise(page_param_first, page_param_second, page_param_third):
    #form = leave_form()
    search_form = SearchForm()
    deny_form = LeaveDenyForm()
    leaves = current_user.paginated_pending_authoriser_requests(page_param_first)
    actioned_leaves = current_user.paginated_actioned_authoriser_requests(page_param_second)
    users = current_user.paginated_authoriser_users(page_param_third)
    return render_template('authorise.html',
                           form=search_form,
                           deny_form=deny_form,
                           leaves=leaves,
                           actioned_leaves=actioned_leaves,
                           users=users,
                           page_param_first=page_param_first,
                           page_param_second=page_param_second,
                           page_param_third=page_param_third
                           )


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
    return redirect(url_for('leave.history'))


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

    if not leave.user.authoriser:
        abort(403)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status == 'Approved':
        abort(403) # Prevent reapproving already approved leave requests

    try:
        if not leave.user.entt:
            raise Exception('The user does not have an entitlement template assigned')

        # Validate time_unit consistency
        if leave.time_unit != leave.user.entt.time_unit:
            raise Exception(
                f"""Leave time unit '{leave.time_unit}' does not match the
                user's current entitlement time unit '{leave.user.entt.time_unit}'"""
            )
        # Add the current user to the actioned_entries relationship
        """
        leave_actioned = LeaveActioned(
                leave_id=leave.id,
                authoriser_id=current_user.id
        )
        """
        leave.status = 'Approved'
        #leave.actioned_by=current_user

        leave.is_deductable()

        leave.save()
        #leave_actioned.save()
    except Exception as e:
        db.session.rollback()
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
    Revoke an approved leave request. Validate time_unit consistency and reinstate
    entitlement.
    TODO - Only authorisers or those with admin.leave update permissions
    can Revoke.
    Detect if leave_type is deductable. If so, allowance will
    be automatically reinstated.

    TODO - rethink: Authorisers should only be able to revoke leaves that have
    start_dates no more than 7 days old from the current day.
    ^ For admins 30 days.

    TODO - test half days
    """
    leave = Leave.query.get_or_404(id)

    if not leave.user.authoriser:
        abort(403)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status != 'Approved':
        abort(403)

    form = LeaveDenyForm()

    if form.validate_on_submit():
        try:
            if not leave.user.entt:
                raise Exception('The user does not have an entitlement template assigned')
            # Validate time_unit consistency
            if leave.time_unit != leave.user.entt.time_unit:
                raise Exception(
                    f"""Leave time unit '{leave.time_unit}' does not match the
                    user's current entitlement time unit '{leave.user.entt.time_unit}'"""
                )

            leave.status = 'Revoked'
            leave.status_details = form.status_details.data

            if leave.ltype.deductable == True:
                # Determine the amount to reinstate

                # Convert the reinstated amount to the user's entitlement time unit
                equivalent_amount = leave.user.entt.convert_entitlement(
                    value=leave.duration,
                    unit=leave.time_unit,  # Use leave's stored time unit
                    target_unit=leave.user.entt.time_unit,
                    hours_per_day=leave.user.entt.working_hours_per_day
                )

                # Reinstate the entitlement
                leave.user.reinstate_allowance_days(equivalent_amount)
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
    """
    leave = Leave.query.get_or_404(id)
    if not leave.user.authoriser:
        abort(403)
    if current_user != leave.user.authoriser:
        abort(403)
    if leave.status != 'Pending':
        abort(403)

    form = LeaveDenyForm()

    if form.validate_on_submit():
        try:
            leave.status = 'Declined'
            leave.status_details = form.status_details.data
            #leave.actioned_by=current_user
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
