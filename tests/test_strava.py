from unittest.mock import patch, MagicMock
from contest.models import Athlete, User
from contest.tasks import strava_sync

def test_strava_sync_runs_without_real_api(db_session, app_fixture):
    # Create a fake athlete in the database
    athlete = Athlete(
        id=123,
        firstname="Test",
        lastname="User",
        country="Testland",
        access_token="token",
        refresh_token="refresh",
        expires_at=9999999999
    )
    db_session.add(athlete)
    db_session.commit()

    # Prepare a fake client with real attributes
    fake_client = MagicMock()
    fake_client.get_athlete.return_value = athlete
    fake_client.get_activities.return_value = []
    fake_client.access_token = "token"
    fake_client.refresh_token = "refresh"
    fake_client.token_expires_at = 9999999999

    with patch("contest.tasks.Client", return_value=fake_client):
        strava_sync(app_fixture)

def test_strava_callback_links_athlete(client, db_session):
    user = User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    fake_token_response = {
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token",
        "expires_at": 9999999999,
    }
    fake_athlete = MagicMock()
    fake_athlete.id = 123
    fake_athlete.firstname = "Test"
    fake_athlete.lastname = "User"
    fake_athlete.country = "Testland"

    with patch("contest.strava.Client") as mock_client_cls, \
         patch("contest.tasks.Client") as mock_tasks_client_cls:
        # For callback
        mock_client = mock_client_cls.return_value
        mock_client.exchange_code_for_token.return_value = fake_token_response
        mock_client.get_athlete.return_value = fake_athlete
        mock_client.access_token = fake_token_response["access_token"]
        mock_client.refresh_token = fake_token_response["refresh_token"]
        mock_client.token_expires_at = fake_token_response["expires_at"]

        # For sync_athlete (once token is exchanged)
        mock_tasks_client = mock_tasks_client_cls.return_value
        mock_tasks_client.get_athlete.return_value = fake_athlete
        mock_tasks_client.access_token = fake_token_response["access_token"]
        mock_tasks_client.refresh_token = fake_token_response["refresh_token"]
        mock_tasks_client.token_expires_at = fake_token_response["expires_at"]

        response = client.get("/strava/callback?code=abc123")
        assert response.status_code == 200

        athlete = Athlete.query.filter_by(id=123).first()
        assert athlete is not None
        assert athlete.firstname == "Test"
        user = db_session.get(User, user.id)
        assert user.athlete_id == 123
