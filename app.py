import datetime
import os
from flask_migrate import upgrade
from flask_apscheduler import APScheduler
from contest import create_app
from contest.tasks import strava_sync, compute
from contest.init_defaults import initialize_defaults


def should_start_scheduler():
    # Retourne True si WERKZEUG_RUN_MAIN ou FLASK_MAIN_PROCESS est 'true',
    # ou si aucune des deux variables n'est définie (cas d'un lancement direct python app.py)
    wzm = os.environ.get("WERKZEUG_RUN_MAIN")
    fmp = os.environ.get("FLASK_MAIN_PROCESS")
    return (
        wzm == "true"
        or fmp == "true"
        or (wzm is None and fmp is None)
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
        app.logger.info("[scheduler] Adding strava_sync_and_compute job")
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
    # Pour la prod : debug=False, host par défaut (127.0.0.1) ou variable d'env
    app.run(debug=app.config.get("FLASK_DEBUG"),
            host=app.config.get("FLASK_RUN_HOST"),
            port=app.config.get("FLASK_DEBUG"))
