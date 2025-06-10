from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user
from .forms import RegistrationForm, LoginForm
from .extensions import db
from .models import User

auth = Blueprint("auth", __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    nologin = False
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            nologin = True
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('views.index'))
    return render_template('login.html', title='Sign In', form=form, message=nologin)


@auth.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('views.index'))
