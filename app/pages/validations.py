from wtforms.validators import ValidationError
from app.pages.models import Page
from sqlalchemy import func

def check_page_route_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    page = Page.query.filter(func.lower(Page.route)==field.data.lower()).first()
    if page:
        raise ValidationError('Route already exists')
