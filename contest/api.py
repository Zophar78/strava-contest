import calendar
from datetime import datetime, date, timedelta
from typing import Tuple
import flask
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from .models import (
    Athlete, Activity, Point
)
from .extensions import db

api = Blueprint("api", __name__)


@api.route("/")
def get_endpoints() -> Tuple[flask.Response, int]:
    endpoints = {
        "athlete_url": "/api/v1/athletes",
    }
    return jsonify(endpoints), 200


@api.route("/athletes", methods=["GET"])
def get_all_athletes() -> Tuple[flask.Response, int]:
    athletes = Athlete.query.order_by(Athlete.firstname, Athlete.lastname).all()
    athletes_array = []
    for athlete in athletes:
        athletes_array.append(athlete.toDict())
    return jsonify(athletes_array), 200


@api.route("/my_activities", methods=["GET"])
@login_required
def get_my_activities():
    if not current_user.athlete_id:
        return jsonify({"error": "No athlete linked"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    activities_query = current_user.athlete.activities.order_by(
        Activity.start_date.desc()
    )
    pagination = activities_query.paginate(page=page, per_page=per_page, error_out=False)
    activities = [a.to_dict() for a in pagination.items]

    return jsonify({
        "activities": activities,
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages
    }), 200


def get_week_data(year, week):
    week_points = (
        Point.query.filter_by(year=year, week_number=week)
        .order_by(Point.total_points.desc())
        .join(Athlete)
        .all()
    )
    return [
        {
            "rank": i + 1,
            "firstname": p.athlete.firstname,
            "lastname": p.athlete.lastname,
            "points": p.total_points
        }
        for i, p in enumerate(week_points)
    ]


def get_month_data(year, month):
    month_weeks = set()
    cal = calendar.Calendar()
    for week_tuple in cal.monthdatescalendar(year, month):
        for day in week_tuple:
            if day.month == month:
                month_weeks.add(day.isocalendar()[1])
    month_points_query = (
        Point.query.filter(Point.year == year, Point.week_number.in_(month_weeks))
        .join(Athlete)
        .with_entities(
            Point.athlete_id,
            Athlete.firstname,
            Athlete.lastname,
            db.func.sum(Point.total_points).label('total_points')
        )
        .group_by(Point.athlete_id, Athlete.firstname, Athlete.lastname)
        .order_by(db.desc('total_points'))
    )
    return [
        {
            "rank": i + 1,
            "firstname": row.firstname,
            "lastname": row.lastname,
            "points": row.total_points
        }
        for i, row in enumerate(month_points_query)
    ]


def get_year_data(year):
    year_points_query = (
        Point.query.filter_by(year=year)
        .join(Athlete)
        .with_entities(
            Point.athlete_id,
            Athlete.firstname,
            Athlete.lastname,
            db.func.sum(Point.total_points).label('total_points')
        )
        .group_by(Point.athlete_id, Athlete.firstname, Athlete.lastname)
        .order_by(db.desc('total_points'))
    )
    return [
        {
            "rank": i + 1,
            "firstname": row.firstname,
            "lastname": row.lastname,
            "points": row.total_points
        }
        for i, row in enumerate(year_points_query)
    ]


@api.route("/leaderboard", methods=["GET"])
def leaderboard():
    today = datetime.today()
    week = int(request.args.get('week', today.isocalendar()[1]))
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    week_data = get_week_data(year, week)
    month_data = get_month_data(year, month)
    year_data = get_year_data(year)

    try:
        week_start = date.fromisocalendar(year, week, 1)
        week_end = week_start + timedelta(days=6)
    except ValueError:
        week_start = week_end = None

    month_name = calendar.month_name[month]

    return jsonify({
        "week": week,
        "month": month,
        "year": year,
        "week_points": week_data,
        "month_points": month_data,
        "year_points": year_data,
        "week_start": week_start.strftime("%a %d %b") if week_start else "",
        "week_end": week_end.strftime("%a %d %b") if week_end else "",
        "month_name": month_name,
    })
