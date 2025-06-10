from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.widgets import ColorInput
from .models import User


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                       Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired()])
    new_password2 = PasswordField(
        'Repeat new password',
        validators=[DataRequired(), EqualTo('new_password', message="Passwords must match")],
    )
    submit = SubmitField('Change Password')


class AdminSiteConfigForm(FlaskForm):
    dashboard_title = StringField("Dashboard Title", validators=[DataRequired()])
    theme = SelectField(
        "Theme",
        choices=[
            ("default", "Bootstrap (Default)"),
            ("cerulean", "Cerulean"),
            ("cosmo", "Cosmo"),
            ("cyborg", "Cyborg (Dark)"),
            ("darkly", "Darkly (Dark)"),
            ("flatly", "Flatly"),
            ("journal", "Journal"),
            ("litera", "Litera"),
            ("lumen", "Lumen"),
            ("lux", "Lux"),
            ("materia", "Materia"),
            ("minty", "Minty"),
            ("morph", "Morph"),
            ("pulse", "Pulse"),
            ("quartz", "Quartz"),
            ("sandstone", "Sandstone"),
            ("simplex", "Simplex"),
            ("sketchy", "Sketchy"),
            ("slate", "Slate (Dark)"),
            ("solar", "Solar"),
            ("spacelab", "Spacelab"),
            ("superhero", "Superhero (Dark)"),
            ("united", "United"),
            ("vapor", "Vapor"),
            ("yeti", "Yeti"),
            ("zephyr", "Zephyr"),
        ],
        validators=[DataRequired()]
    )
    primary_color = StringField(
        "Primary color (for default theme)",
        widget=ColorInput(),
        default="#0d6efd"
    )
    logo = FileField(
        "Logo (PNG/JPG)",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")]
    )
    banner = TextAreaField("Homepage Disclaimer/Banner")
    submit = SubmitField("Save")
