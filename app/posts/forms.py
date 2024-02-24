from app.posts.models import Post
from flask_admin.form.widgets import Select2Widget
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.validators import (DataRequired, Optional, ValidationError,
                                Email, Length, EqualTo)
from wtforms import (StringField, SubmitField, TextAreaField,
                     SelectField, HiddenField)



class PostForm(FlaskForm):
    name = StringField('Title', validators=[DataRequired(), Length(min=2, max=150)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=2, max=30000)], render_kw={'id': 'ckeditor'})


class CommentForm(FlaskForm):
    text = TextAreaField('Your Comment', validators=[DataRequired(), Length(min=2, max=30000)], render_kw={'id': 'ckeditor'})


class SearchForm(FlaskForm):
    q = StringField('Search terms', [Optional(), Length(1, 256)])
