from .models import User, SiteConfig
from .extensions import db

def initialize_defaults(flask_app):
    with flask_app.app_context():
        admin_email = flask_app.config["ADMIN_EMAIL"]
        admin_password = flask_app.config["ADMIN_PASSWORD"]
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            user = User(
                email=admin_email,
                is_admin=True
            )
            user.set_password(admin_password)
            db.session.add(user)
        if not SiteConfig.query.filter_by(key="dashboard_title").first():
            db.session.add(SiteConfig(key="dashboard_title", value="Strava Contest"))
        if not SiteConfig.query.filter_by(key="banner").first():
            db.session.add(SiteConfig(
                key="banner",
                value="""
<strong>Want to join the Strava Contest?</strong>
<ul class="text-start mt-2 mb-2" style="margin-left:1.5em;">
  <li>Register on this dashboard with your email address</li>
  <li>Create a Strava account (if you don't already have one)</li>
  <li>Go to your profile page to link your Strava account</li>
</ul>
<div class="text-muted" style="font-size:0.95em;">
  Your Strava activities will be automatically synchronized for the leaderboard.
</div>
""".strip()
            ))
        db.session.commit()
