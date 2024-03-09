from app.event.models import EventType
from app.event.validations import (check_end_date,
                                   check_leave_year_start,
                                   check_allowance,
                                   check_approval
                                   )
import datetime
from flask_admin.form.widgets import Select2Widget
from flask_wtf import FlaskForm
from wtforms import (Form, StringField, SubmitField, TextAreaField, BooleanField)
from wtforms.fields import DateField as DatePickerField
from wtforms.fields import TimeField, SelectField
from wtforms.validators import (DataRequired, Length, Optional)
from wtforms_alchemy import QuerySelectField
from wtforms_components import DateRange


class EventForm(FlaskForm):
    start_date = DatePickerField('Start Date',
                                 validators=[check_leave_year_start, DataRequired()]
                                 )
    end_date = DatePickerField('End Date',
                               validators=[check_end_date, DataRequired()]
                               )
    etype = QuerySelectField('Event Type',
                             query_factory = lambda: EventType.query.filter(EventType.active==True).all(),
                             get_pk=lambda et: et.id, widget=Select2Widget(),
                             allow_blank=False,
                             validators=[DataRequired(),check_approval],
                             render_kw={"id": "event-type-select"}
                             )
    details = TextAreaField('Details',
                            validators=[Optional(), Length(min=2, max=1000)],
                            render_kw={"placeholder": "(Optional)"}
                            )
    #submit = SubmitField('Submit', validators=[check_allowance], render_kw={'id': 'submitRequestBtn'})
    submit = SubmitField('Submit', render_kw={'id': 'submitRequestBtn'})


class EventHalfDayForm(EventForm):
    end_date = DatePickerField('End Date', validators=[check_end_date])
    half_day = BooleanField(label='Half Day')


class EventDenyForm(FlaskForm):
    status_details = TextAreaField('Reason', validators=[DataRequired(), Length(min=5,max=120)])
