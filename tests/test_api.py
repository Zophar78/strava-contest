# pylint: disable=unused-argument,redefined-outer-name

import pytest
from contest.models import Athlete, Point, Activity, User

@pytest.fixture
def sample_data(db_session):
    # Create three athletes
    a1 = Athlete(firstname="Alice", lastname="Test")
    a2 = Athlete(firstname="Bob", lastname="Demo")
    a3 = Athlete(firstname="Charlie", lastname="Sample")
    db_session.add_all([a1, a2, a3])
    db_session.commit()

    # Points for week 1, month 1, year 2025
    p1 = Point(year=2025, week_number=1, athlete_id=a1.id, total_points=10)
    p2 = Point(year=2025, week_number=1, athlete_id=a2.id, total_points=5)
    p3 = Point(year=2025, week_number=1, athlete_id=a3.id, total_points=8)
    # Points for week 2, same year
    p4 = Point(year=2025, week_number=2, athlete_id=a1.id, total_points=7)
    p5 = Point(year=2025, week_number=2, athlete_id=a2.id, total_points=12)
    # Points for week 3, same year
    p6 = Point(year=2025, week_number=3, athlete_id=a3.id, total_points=15)
    # Points for another year
    p7 = Point(year=2024, week_number=1, athlete_id=a1.id, total_points=20)
    db_session.add_all([p1, p2, p3, p4, p5, p6, p7])
    db_session.commit()

def test_leaderboard_api(client, sample_data):
    response = client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    data = response.get_json()
    assert "week" in data
    assert "month" in data
    assert "year" in data
    assert "week_points" in data
    assert "month_points" in data
    assert "year_points" in data
    assert isinstance(data["week_points"], list)
    assert isinstance(data["month_points"], list)
    assert isinstance(data["year_points"], list)

def test_leaderboard_api_with_params(client, sample_data):
    response = client.get("/api/v1/leaderboard?week=1&month=1&year=2025")
    assert response.status_code == 200
    data = response.get_json()
    assert data["week"] == 1
    assert data["month"] == 1
    assert data["year"] == 2025
    # Check that points are present for all athletes
    names = {row["firstname"]: row["points"] for row in data["week_points"]}
    assert names["Alice"] == 10
    assert names["Bob"] == 5
    assert names["Charlie"] == 8

def test_leaderboard_api_month_aggregation(client, sample_data):
    # Check monthly aggregation (sum of points over several weeks)
    response = client.get("/api/v1/leaderboard?month=1&year=2025")
    assert response.status_code == 200
    data = response.get_json()
    # Alice: 10 (w1) + 7 (w2) = 17, Bob: 5 (w1) + 12 (w2) = 17, Charlie: 8 (w1) + 15 (w3) = 23
    points = {row["firstname"]: row["points"] for row in data["month_points"]}
    assert points["Alice"] == 17
    assert points["Bob"] == 17
    assert points["Charlie"] == 23

def test_leaderboard_api_year_aggregation(client, sample_data):
    # Check yearly aggregation (sum of points over all weeks of the year)
    response = client.get("/api/v1/leaderboard?year=2025")
    assert response.status_code == 200
    data = response.get_json()
    points = {row["firstname"]: row["points"] for row in data["year_points"]}
    # Alice: 10+7=17, Bob: 5+12=17, Charlie: 8+15=23
    assert points["Alice"] == 17
    assert points["Bob"] == 17
    assert points["Charlie"] == 23

def test_leaderboard_api_empty(client):
    response = client.get("/api/v1/leaderboard?week=99&month=12&year=2099")
    assert response.status_code == 200
    data = response.get_json()
    assert data["week_points"] == []
    assert data["month_points"] == []
    assert data["year_points"] == []

def test_my_activities_authenticated(client, db_session):
    # Check activities for an authenticated user linked to an athlete
    athlete = Athlete(firstname="Test", lastname="User")
    db_session.add(athlete)
    db_session.commit()

    user = User(email="test@example.com")
    user.athlete_id = athlete.id
    db_session.add(user)
    db_session.commit()

    act1 = Activity(
        id=1,
        athlete_id=athlete.id,
        name="Workout 1",
        distance=10.0,
        moving_time=3600,
        elapsed_time=3700,
        start_date=None,
        total_elevation_gain=100,
        type="Run",
        has_map=0,
        polyline=None,
        photo_count=0,
    )
    db_session.add(act1)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = client.get("/api/v1/my_activities")
    assert response.status_code == 200
    data = response.get_json()
    assert "activities" in data
    assert isinstance(data["activities"], list)
    assert len(data["activities"]) == 1
    assert data["activities"][0]["name"] == "Workout 1"

def test_my_activities_no_athlete(client, db_session):
    # Check error when user has no linked athlete
    user = User(email="noathlete@example.com")
    db_session.add(user)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = client.get("/api/v1/my_activities")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
