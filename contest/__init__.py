import logging
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from .extensions import db
from .models import User
from .api import api
from .auth import auth
from .strava import strava
from .views import views

migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config)  -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging
    app.logger.setLevel(logging.INFO)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    logging.basicConfig()
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    # Login Manager
    login = LoginManager(app)
    login.login_view = 'auth.login'

    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    # Register blueprints
    app.register_blueprint(api, url_prefix="/api/v1")
    app.register_blueprint(views)
    app.register_blueprint(auth)
    app.register_blueprint(strava, url_prefix="/strava")

    ## Error handlers
    @app.errorhandler(404)
    def page_not_found(_):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def page_forbidden(_):
        return render_template('403.html'), 403

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception("Unhandled Exception: %s", e)
        return render_template("500.html", error=e), 500

    return app
