from flask import render_template, request, url_for, redirect, flash, abort, Blueprint, current_app
from flask_login import login_required
from sqlalchemy import func, text

from app.decorators import setup_required
from app.pages.models import Page

pages = Blueprint('pages', __name__, template_folder='templates')

@pages.before_request
@setup_required()
@login_required
def before_request():
    pass


@pages.route('/<path:route>')
@login_required
def index(route):
    """
    Route in charge or routing users to Custom Pages
    """
    page = Page.query.filter(Page.active==True).filter(Page.route==route).first_or_404()
    return render_template('page.html', page=page)
