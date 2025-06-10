# pylint: disable=unused-argument,redefined-outer-name

from datetime import datetime, timedelta
import pytest
from contest.rules import Standard, RegularityBonusA, RegularityBonusB, ContestEngine
from contest import rules

class DummyActivity:  # pylint: disable=too-few-public-methods
    """Dummy activity for testing."""
    def __init__(self, start_date):
        self.start_date = start_date

class DummyAthlete:  # pylint: disable=too-few-public-methods
    """Dummy athlete for testing."""
    def __init__(self, athlete_id):
        self.id = athlete_id

@pytest.fixture
def activities_fixture():
    today = datetime.now()
    # 4 activities on different days
    return [
        DummyActivity(today),
        DummyActivity(today - timedelta(days=1)),
        DummyActivity(today - timedelta(days=2)),
        DummyActivity(today - timedelta(days=3)),
    ]

def test_standard_rule(activities_fixture):
    rule = Standard(points_per_activity=1)
    athlete = DummyAthlete(1)
    assert rule.calculate_points(athlete, activities_fixture) == 4

def test_regularity_bonus_b(activities_fixture):
    rule = RegularityBonusB(bonus_points=2)
    athlete = DummyAthlete(1)
    assert rule.calculate_points(athlete, activities_fixture) == 2

def test_regularity_bonus_a(monkeypatch, activities_fixture):
    # Simule une activité la semaine précédente
    def fake_get_valid_activities(_start, _end, _athlete_id):
        return [DummyActivity(datetime.now() - timedelta(days=7))]
    monkeypatch.setattr(rules, "get_valid_activities", fake_get_valid_activities)
    rule = RegularityBonusA(bonus_points=2, week_number=2, year=2025)
    athlete = DummyAthlete(1)
    assert rule.calculate_points(athlete, activities_fixture) == 2

def test_regularity_bonus_a_year_change(monkeypatch):
    # Semaine 1, activité la dernière semaine de l'année précédente
    def fake_get_valid_activities(_start, _end, _athlete_id):
        return [DummyActivity(datetime(2024, 12, 31))]
    monkeypatch.setattr(rules, "get_valid_activities", fake_get_valid_activities)
    rule = RegularityBonusA(bonus_points=2, week_number=1, year=2025)
    athlete = DummyAthlete(1)
    activities_local_year = [DummyActivity(datetime(2025, 1, 2))]
    assert rule.calculate_points(athlete, activities_local_year) == 2

def test_no_activities():
    rule_std = Standard(points_per_activity=1)
    rule_reg_a = RegularityBonusA(bonus_points=2, week_number=2, year=2025)
    rule_reg_b = RegularityBonusB(bonus_points=2)
    athlete = DummyAthlete(1)
    empty = []
    assert rule_std.calculate_points(athlete, empty) == 0
    assert rule_reg_a.calculate_points(athlete, empty) == 0
    assert rule_reg_b.calculate_points(athlete, empty) == 0

def test_multiple_activities_same_day():
    today = datetime.now()
    activities_same_day = [
        DummyActivity(today),
        DummyActivity(today),  # même jour
        DummyActivity(today - timedelta(days=1)),
    ]
    rule = Standard(points_per_activity=1)
    athlete = DummyAthlete(1)
    assert rule.calculate_points(athlete, activities_same_day) == 2  # 2 jours uniques

def test_regularity_bonus_b_not_enough_days():
    today = datetime.now()
    activities_not_enough = [
        DummyActivity(today),
        DummyActivity(today - timedelta(days=1)),
        DummyActivity(today - timedelta(days=2)),
    ]
    rule = RegularityBonusB(bonus_points=2)
    athlete = DummyAthlete(1)
    assert rule.calculate_points(athlete, activities_not_enough) == 0  # moins de 4 jours uniques

def test_contest_engine_sum(monkeypatch, activities_fixture):
    def fake_get_valid_activities(_start, _end, _athlete_id):
        return activities_fixture
    monkeypatch.setattr(rules, "get_valid_activities", fake_get_valid_activities)
    rules_list = [
        Standard(points_per_activity=1),
        RegularityBonusB(bonus_points=2)
    ]
    engine = ContestEngine(rules_list, 2025)
    athlete = DummyAthlete(1)
    points_by_week = engine.calculate_points_for_all_weeks(athlete)
    # All weeks should have the same points (6)
    for pts in points_by_week.values():
        assert pts == 6
