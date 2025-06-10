import time
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from flask import current_app
from .models import Athlete, Activity

def week_boundaries(year: int, week: int):
    """Return starting 'monday' and ending 'sunday' date for a given year and week."""
    return {
        'first_monday': date.fromisocalendar(year, week, 1),
        'last_sunday': date.fromisocalendar(year, week, 7)
    }

def get_valid_activities(start_timestamp, end_timestamp, athlete_id):
    """Return all valid activities for an athlete in a period."""
    min_time = current_app.config['MINIMUM_ACTIVITY_TIME']
    return Activity.query.filter(
        Activity.start_date >= datetime.fromtimestamp(start_timestamp),
        Activity.start_date <= datetime.fromtimestamp(end_timestamp),
        Activity.athlete_id == athlete_id,
        Activity.moving_time >= min_time
    ).all()

def unique_activity_days(activities):
    """Return a set of unique days (date objects) with at least one activity."""
    return set(a.start_date.date() for a in activities)

class Rule(ABC):
    """Base interface for scoring rules."""
    @abstractmethod
    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        """Calculate the number of points for the athlete."""

class Standard(Rule):
    """1 point per activity (minimum duration, max one per day)."""
    def __init__(self, points_per_activity: int):
        self.points_per_activity = points_per_activity

    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        days = unique_activity_days(activities)
        return len(days) * self.points_per_activity

class RegularityBonusA(Rule):
    """Bonus if at least one activity this week and at least one last week."""
    def __init__(self, bonus_points: int, week_number: int, year: int):
        self.bonus_points = bonus_points
        self.week_number = week_number
        self.year = year

    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        if not activities:
            return 0
        # Calculate last week (handle year change)
        if self.week_number == 1:
            prev_year = self.year - 1
            prev_week = date(prev_year, 12, 28).isocalendar()[1]
        else:
            prev_year = self.year
            prev_week = self.week_number - 1
        last_week_range = week_boundaries(prev_year, prev_week)
        last_week_activities = get_valid_activities(
            time.mktime(last_week_range['first_monday'].timetuple()),
            time.mktime(last_week_range['last_sunday'].timetuple()),
            athlete.id
        )
        if last_week_activities:
            return self.bonus_points
        return 0

class RegularityBonusB(Rule):
    """Bonus for at least 4 unique activity days in the week."""
    def __init__(self, bonus_points: int):
        self.bonus_points = bonus_points

    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        days = unique_activity_days(activities)
        return self.bonus_points if len(days) >= 4 else 0

class ContestEngine:
    """Main ContestEngine to compute points/rules"""
    def __init__(self, rules: list[Rule], year: int):
        self.rules = rules
        self.year = year

    def _weeks_to_compute(self, current_year, current_week):
        """Generate all (year, week) tuples to compute for the contest."""
        prev_year = self.year - 1
        last_week_prev_year = date(prev_year, 12, 28).isocalendar()[1]
        weeks = [(prev_year, last_week_prev_year)]
        for week in range(1, 54):
            try:
                week_start = date(self.year, 1, 4) + timedelta(weeks=week-1)
                week_year, week_num = week_start.isocalendar()[:2]
                if week_year != self.year or week_num != week:
                    continue
            except ValueError:
                continue
            if (self.year > current_year) or (self.year == current_year and week > current_week):
                break
            weeks.append((self.year, week))
        return weeks

    def calculate_points_for_all_weeks(self, athlete: Athlete) -> dict:
        results = {}
        today = datetime.now()
        current_year, current_week = today.isocalendar()[:2]

        weeks_to_compute = self._weeks_to_compute(current_year, current_week)

        for year, week in weeks_to_compute:
            week_range = week_boundaries(year, week)
            activities = get_valid_activities(
                time.mktime(week_range['first_monday'].timetuple()),
                time.mktime(week_range['last_sunday'].timetuple()),
                athlete.id
            )
            points = 0
            for rule in self.rules:
                if isinstance(rule, RegularityBonusA):
                    points += RegularityBonusA(rule.bonus_points, week, year).calculate_points(
                        athlete, activities
                    )
                else:
                    points += rule.calculate_points(athlete, activities)
            results[(year, week)] = points

        return results
