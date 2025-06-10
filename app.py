import datetime
import os
import sys
from flask_migrate import upgrade
from flask_apscheduler import APScheduler
from contest import create_app
from contest.tasks import strava_sync, compute
from contest.init_defaults import initialize_defaults


def should_start_scheduler():
    return (
        os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        or os.environ.get("FLASK_MAIN_PROCESS") == "true"
    )

def sync_and_compute(flask_app):
    strava_sync(flask_app)
    compute(flask_app)

def ensure_db_up_to_date(flask_app):
    with flask_app.app_context():
        upgrade()

app = create_app()
ensure_db_up_to_date(app)
initialize_defaults(app)

# Initialize the scheduler and avoid multiple instances
if should_start_scheduler():
    scheduler = APScheduler()
    scheduler.init_app(app)
    if not app.config.get("TESTING", False):
        print("[scheduler] Adding strava_sync_and_compute job")
        scheduler.add_job(
            id="strava_sync_and_compute",
            func=sync_and_compute,
            trigger='interval',
            minutes=15,
            args=[app],
            replace_existing=True,
            next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10)
        )
        scheduler.start()


if __name__ == "__main__":  # pragma: no cover
    # Start the Flask application
    app.run(debug=True, host="0.0.0.0", port=8080)
