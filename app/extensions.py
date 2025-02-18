from flask_continuum import Continuum
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_authorize import Authorize

db = SQLAlchemy()

continuum = Continuum(db=db, user_cls='User')
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
debug_toolbar = DebugToolbarExtension()
