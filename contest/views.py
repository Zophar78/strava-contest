from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .forms import ChangePasswordForm, AdminSiteConfigForm
from .extensions import db
from .models import SiteConfig

views = Blueprint("views", __name__)

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return func(*args, **kwargs)
    return wrapper

@views.app_context_processor
def inject_theme():
    dark_themes = ['cyborg', 'darkly', 'slate', 'superhero']
    config = {c.key: c.value for c in SiteConfig.query.all()}
    site_theme = config.get("theme", "default")
    site_primary_color = config.get("primary_color", "#0d6efd")
    dashboard_title = config.get("dashboard_title", "Strava Contest")
    banner = config.get("banner", None)
    return {
        "site_theme": site_theme,
        "navbar_class": "navbar-dark" if site_theme in dark_themes else "navbar-light",
        "site_primary_color": site_primary_color,
        "dashboard_title": dashboard_title,
        "banner": banner,
    }

@views.route("/")
def index():
    return render_template('index.html')

@views.route('/profile', methods=['GET'], strict_slashes=False)
@login_required
def profile():
    return render_template(
        'profile.html',
        user=current_user
    )

@views.route('/profile/password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Incorrect current password.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('views.change_password'))
    return render_template('change_password.html', form=form)

@views.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/admin.html")

@views.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    config = {c.key: c.value for c in SiteConfig.query.all()}
    form = AdminSiteConfigForm(
        dashboard_title=config.get("dashboard_title", "Strava Contest"),
        theme=config.get("theme", "default"),
        primary_color=config.get("primary_color", "#0d6efd"),
        logo=config.get("logo_path"),
        banner=config.get("banner", "")
    )
    if form.validate_on_submit():
        # Save dashboard_title
        title_row = SiteConfig.query.filter_by(key="dashboard_title").first()
        if not title_row:
            title_row = SiteConfig(key="dashboard_title")
            db.session.add(title_row)
        title_row.value = form.dashboard_title.data

        theme = form.theme.data
        theme_row = SiteConfig.query.filter_by(key="theme").first()
        if theme == "default":
            # Remove the theme entry if it exists
            if theme_row:
                db.session.delete(theme_row)
            color = form.primary_color.data or "#0d6efd"
            color_row = SiteConfig.query.filter_by(key="primary_color").first()
            if not color_row:
                color_row = SiteConfig(key="primary_color")
                db.session.add(color_row)
            color_row.value = color
        else:
            if not theme_row:
                theme_row = SiteConfig(key="theme")
                db.session.add(theme_row)
            theme_row.value = theme
            # Delete primary_color row if it exists
            color_row = SiteConfig.query.filter_by(key="primary_color").first()
            if color_row:
                db.session.delete(color_row)

        # Save logo file if uploaded
        if form.logo.data:
            logo_file = form.logo.data
            logo_path = "static/uploads/logo.png"
            logo_file.save(logo_path)
            logo_row = SiteConfig.query.filter_by(key="logo_path").first()
            if not logo_row:
                logo_row = SiteConfig(key="logo_path")
                db.session.add(logo_row)
            logo_row.value = logo_path

        # Save banner text
        banner_row = SiteConfig.query.filter_by(key="banner").first()
        if not banner_row:
            banner_row = SiteConfig(key="banner")
            db.session.add(banner_row)
        banner_row.value = form.banner.data
        db.session.commit()

        flash("Settings updated!", "success")
        return redirect(url_for("views.admin_settings"))

    return render_template("admin/settings.html", form=form, config=config)
