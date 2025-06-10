from datetime import datetime
from contest.models import User, Athlete, Activity, Point

def test_user_password_hashing(db_session):
    user = User(email='strava-contest@test.com')
    user.set_password('StravaIsAwesome!')
    db_session.add(user)
    db_session.commit()
    assert user.check_password('StravaIsAwesome!')
    assert not user.check_password('wrongpassword')

def test_athlete_creation(db_session):
    athlete = Athlete(firstname="Alice", lastname="Test")
    db_session.add(athlete)
    db_session.commit()
    assert athlete.id is not None
    assert athlete.firstname == "Alice"
    assert athlete.lastname == "Test"

def test_activity_creation_and_relationship(db_session):
    athlete = Athlete(firstname="Bob", lastname="Runner")
    db_session.add(athlete)
    db_session.commit()
    activity = Activity(
        id=1,
        athlete_id=athlete.id,
        name="Morning Run",
        start_date=datetime(2024, 6, 1, 7, 0),
        distance=10000
    )
    db_session.add(activity)
    db_session.commit()
    assert activity.id is not None
    assert activity.athlete_id == athlete.id
    # Test backref
    assert activity in athlete.activities

def test_point_model(db_session):
    athlete = Athlete(firstname="Charlie", lastname="Cyclist")
    db_session.add(athlete)
    db_session.commit()
    point = Point(
        year=2024,
        week_number=23,
        athlete_id=athlete.id,
        total_points=42
    )
    db_session.add(point)
    db_session.commit()
    assert point.athlete_id == athlete.id
    assert point.total_points == 42
