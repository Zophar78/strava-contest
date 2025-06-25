import time
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from flask import current_app
from .models import Athlete, Activity

# --- Helpers ---

def week_boundaries(year: int, week: int) -> dict:
    """Return the Monday and Sunday dates for a given ISO year/week."""
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

def unique_activity_days(activities) -> set:
    """Return a set of unique days (date objects) with at least one activity."""
    return {a.start_date.date() for a in activities}

# --- Rules ---

class Rule(ABC):
    """Base interface for scoring rules."""
    @abstractmethod
    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        pass

    @staticmethod
    def filter_valid_activities(activities):
        min_time = current_app.config['MINIMUM_ACTIVITY_TIME']
        return [a for a in activities if getattr(a, 'moving_time', 0) >= min_time]

class Standard(Rule):
    """1 point per activity (minimum duration, max one per day)."""
    def __init__(self, points_per_activity: int):
        self.points_per_activity = points_per_activity

    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        valid_activities = self.filter_valid_activities(activities)
        return len(unique_activity_days(valid_activities)) * self.points_per_activity

class RegularityBonusA(Rule):
    """
    2 bonus points for the first activity of the week following a week with at least one activity.
    The first week of the month considers the last week of the previous month.
    """
    def __init__(self, bonus_points: int):
        self.bonus_points = bonus_points

    def calculate_points(self, athlete: Athlete, activities: list) -> int:
        valid_activities = self.filter_valid_activities(activities)
        if not valid_activities:
            return 0
        # Use the first activity of the week to determine the week and year
        first_activity = min(valid_activities, key=lambda a: a.start_date)
        year, week = first_activity.start_date.isocalendar()[:2]
        # Previous week (handle month/year change)
        if week == 1:
            # Find the last week of the previous month
            prev_month = first_activity.start_date.replace(day=1) - timedelta(days=1)
            prev_year, prev_week = prev_month.isocalendar()[:2]
        else:
            prev_year = year
            prev_week = week - 1
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
        valid_activities = self.filter_valid_activities(activities)
        return self.bonus_points if len(unique_activity_days(valid_activities)) >= 4 else 0

# --- Engine ---

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
            if (self.year >  current_year) or (self.year == current_year and week > current_week):
                break
            weeks.append((self.year, week))
        return weeks

    def calculate_points_for_all_weeks(self, athlete: Athlete) -> dict:
        results = {}
        today = datetime.now()
        current_year, current_week = today.isocalendar()[:2]
        for year, week in self._weeks_to_compute(current_year, current_week):
            week_range = week_boundaries(year, week)
            activities = get_valid_activities(
                time.mktime(week_range['first_monday'].timetuple()),
                time.mktime(week_range['last_sunday'].timetuple()),
                athlete.id
            )
            points = sum(
                rule.calculate_points(athlete, activities)
                for rule in self.rules
            )
            results[(year, week)] = points
        return results

# --- Dynamic rule loader ---

RULES_REGISTRY = {
    "Standard": Standard,
    "RegularityBonusA": RegularityBonusA,
    "RegularityBonusB": RegularityBonusB,
}

def build_rules_from_config(config):
    rules = []
    for rule_conf in config:
        name = rule_conf["name"]
        args = rule_conf.get("args", {})
        rule_cls = RULES_REGISTRY[name]
        rules.append(rule_cls(**args))
    return rules
