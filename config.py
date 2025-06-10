import os

class Config:  # pylint: disable=too-few-public-methods
    env = os.environ.get('STRAVACONTEST_ENV') or 'prod'
    STRAVACONTEST_DATA_ROOT=os.environ.get('STRAVACONTEST_DATA_ROOT') or os.path.abspath(os.path.dirname(__file__))
    DATABASE_ENGINE = 'sqlite'
    DATABASE_FILE = os.environ.get('DATABASE_FILE') or os.path.join(STRAVACONTEST_DATA_ROOT, 'db.sqlite')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_FILE}"

    # STRAVA API
    STRAVA_REDIRECT_URI = os.environ.get('STRAVA_REDIRECT_URI') or 'http://localhost:5000/strava_callback'
    STRAVA_CLIENT_ID=os.environ.get('STRAVA_CLIENT_ID') or 'XXXX'
    STRAVA_CLIENT_SECRET=os.environ.get('STRAVA_CLIENT_SECRET') or 'changeme'
    # Fetch activities from the last {STRAVA_REFRESH_INTERVAL} months
    STRAVA_REFRESH_INTERVAL=os.environ.get('STRAVA_REFRESH_INTERVAL') or 12

    # WTF Form crsf
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Contest settings
    MINIMUM_ACTIVITY_TIME = os.environ.get('MINIMUM_ACTIVITY_TIME') or 20 * 60

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

class TestConfig(Config):  # pylint: disable=too-few-public-methods
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    TESTING = True
