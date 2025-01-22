from app.user.models import User
from sqlalchemy.sql import case
from app.admin.utils import get_settings_value
from app.department.models import Department, DepartmentMembers
from app.decorators import setup_required
from flask import render_template, request, url_for, redirect, flash, abort, Blueprint, current_app
from flask_login import login_required
from sqlalchemy import func, text

department = Blueprint('department', __name__, template_folder='templates')

@department.before_request
@setup_required()
@login_required
def before_request():
    """
    Protect all post endpoints
    with login_required
    """
    pass

@department.route('/departments', defaults={'page': 1}, methods=['GET', 'POST'])
@department.route('/departments/page/<int:page>', methods=['GET', 'POST'])
def all(page):
    from app.admin.forms import SearchForm
    search_form = SearchForm()
    paginated_departments = Department.query \
        .filter(Department.active) \
        .filter(Department.search((request.args.get('q', text(''))))) \
        .order_by(Department.name.asc(),) \
        .paginate(page, 30, True)
    return render_template('departments.html', departments=paginated_departments, form=search_form)


@department.route('/departments/<int:id>', defaults={'page': 1},  methods=['GET', 'POST'])
@department.route('/departments/<int:id>/page/<int:page>', methods=['GET', 'POST'])
def info(id, page):
    department = Department.query.get_or_404(id)

    # Query users in the department and prioritize the head of department
    paginated_members = User.query \
        .join(DepartmentMembers, DepartmentMembers.user_id == User.id) \
        .filter(DepartmentMembers.department_id == id) \
        .order_by(
            case(
                [(User.id == department.head_id, 0)], else_=1
            ).asc(),  # Head of department first
            User.created_at.asc()  # Then order by username ascending
        ) \
        .paginate(page, 30, True)
    return render_template('department.html', department=department, members=paginated_members)
