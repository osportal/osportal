from app.models import EnttLeaveTypes
from app.leave.models import LeaveType
from app.leave.validations import (check_end_date,
                                   check_leave_year_start,
                                   check_allowance,
                                   check_approval
                                   )
import datetime
from flask_admin.form.widgets import Select2Widget
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (Form, StringField, SubmitField, TextAreaField, BooleanField)
from wtforms.fields import DateField as DatePickerField
from wtforms.fields import TimeField, SelectField
from wtforms.validators import (DataRequired, Length, Optional)
from wtforms_alchemy import QuerySelectField
from wtforms_components import DateRange


class LeaveForm(FlaskForm):
    start_date = DatePickerField('Start Date',
                                 validators=[check_leave_year_start, DataRequired()]
                                 )
    end_date = DatePickerField('End Date',
                               validators=[check_end_date, DataRequired()]
                               )
    entt_ltype = QuerySelectField('Leave Type',
                             query_factory = lambda: EnttLeaveTypes.query.filter(EnttLeaveTypes.entt_id==current_user.get_entt_id()).all(),
                             get_pk=lambda eat: eat.leave_type_id, widget=Select2Widget(),
                             allow_blank=False,
                             validators=[DataRequired(), check_approval],
                             render_kw={"id": "leave-type-select"}
                             )
    details = TextAreaField('Details',
                            validators=[Optional(), Length(min=2, max=1000)],
                            render_kw={"placeholder": "(Optional)"}
                            )
    submit = SubmitField('Submit', validators=[check_allowance], render_kw={'id': 'submitRequestBtn'})
    #submit = SubmitField('Submit', render_kw={'id': 'submitRequestBtn'})


class LeaveHalfDayForm(LeaveForm):
    end_date = DatePickerField('End Date', validators=[check_end_date])
    half_day = BooleanField(label='Half Day')


class LeaveDenyForm(FlaskForm):
    status_details = TextAreaField('Reason', validators=[DataRequired(), Length(min=4,max=120)])
