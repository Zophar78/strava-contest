from datetime import datetime
import dateutil.relativedelta
from flask import current_app
from stravalib import Client
from .extensions import db
from .rules import ContestEngine, Standard, RegularityBonusA, RegularityBonusB
from .models import Athlete, Activity, Point

def sync_athlete(athlete):
    """Synchronize a single athlete's details and activities from Strava."""

    today = datetime.today()
    client = Client(
        access_token=athlete.access_token,
        refresh_token=athlete.refresh_token,
    )
    client.client_id = current_app.config["STRAVA_CLIENT_ID"]
    client.client_secret = current_app.config["STRAVA_CLIENT_SECRET"]
    client.token_expires = athlete.expires_at

    # Refresh athlete details
    current_app.logger.info('Refreshing athlete details from Strava API')
    athlete_detail = client.get_athlete()
    Athlete.query.filter_by(id=athlete_detail.id).update({
        "firstname": athlete_detail.firstname,
        "lastname": athlete_detail.lastname,
        "country": athlete_detail.country
    })
    db.session.commit()

    # If the token was refreshed, update the DB
    if client.access_token != athlete.access_token:
        athlete.access_token = client.access_token
        athlete.refresh_token = client.refresh_token
        athlete.expires_at = getattr(client, "token_expires_at", athlete.expires_at)
        db.session.commit()

    # Refresh athlete activities
    current_app.logger.info(
        'Refreshing activities for %s (%d)', athlete.firstname, athlete.id
    )
    activities = client.get_activities(
        after=(
            today - dateutil.relativedelta.relativedelta(
                months=current_app.config["STRAVA_REFRESH_INTERVAL"]
            )
        )
    )
    for activity_item in activities:
        activity_record = Activity.query.filter_by(id=activity_item.id)
        if not activity_record.first():
            # Insert activity
            activity_record = Activity(
                id=activity_item.id,
                athlete_id=athlete.id,
                name=activity_item.name,
                distance=activity_item.distance,
                moving_time=activity_item.moving_time,
                elapsed_time=activity_item.elapsed_time,
                start_date=activity_item.start_date,
                total_elevation_gain=activity_item.total_elevation_gain,
                type=activity_item.type.root,
                photo_count=activity_item.photo_count,
                has_map=1 if activity_item.map else 0,
                polyline=activity_item.map.polyline if activity_item.map else None,
            )
            db.session.add(activity_record)
        else:
            # Update activity
            activity_record.update({
                "name": activity_item.name,
                "distance": activity_item.distance,
                "moving_time": activity_item.moving_time,
                "elapsed_time": activity_item.elapsed_time,
                "start_date": activity_item.start_date,
                "total_elevation_gain": activity_item.total_elevation_gain,
                "type": activity_item.type.root,
                "photo_count": activity_item.photo_count
            })
        db.session.commit()
    current_app.logger.info('Activities successfully refreshed for athlete %s', athlete.firstname)


def strava_sync(app):
    """Synchronize all athletes."""
    with app.app_context():
        athletes = Athlete.query.all()
        for athlete in athletes:
            sync_athlete(athlete)


def compute_athlete_points(athlete):
    """
    Compute points for a single athlete for every week where they have activities.
    Only store points > 0, and ensure no DB entry exists for weeks with 0 points.
    """
    activities = Activity.query.filter_by(athlete_id=athlete.id).all()
    weeks = set()
    for activity in activities:
        year, week = activity.start_date.isocalendar()[:2]
        weeks.add((year, week))

    for year, week in weeks:
        week_activities = [
            a for a in activities
            if a.start_date.isocalendar()[:2] == (year, week)
        ]
        rules = [
            Standard(points_per_activity=1),
            RegularityBonusA(bonus_points=2, week_number=week, year=year),
            RegularityBonusB(bonus_points=2),
        ]
        engine = ContestEngine(rules, year)
        points = 0
        for rule in rules:
            if isinstance(rule, RegularityBonusA):
                points += RegularityBonusA(rule.bonus_points, week, year).calculate_points(
                    athlete, week_activities
                )
            else:
                points += rule.calculate_points(athlete, week_activities)

        existing = Point.query.filter_by(year=year, week_number=week, athlete_id=athlete.id).first()
        if points > 0:
            if existing:
                existing.total_points = points
            else:
                db.session.add(Point(
                    year=year, week_number=week, athlete_id=athlete.id, total_points=points
                ))
        else:
            if existing:
                db.session.delete(existing)
    db.session.commit()


def compute(app):
    """
    Compute points for all athletes.
    """
    with app.app_context():
        for athlete in Athlete.query.all():
            compute_athlete_points(athlete)
