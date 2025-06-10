#pylint: disable=redefined-outer-name
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from contest import create_app
from contest.extensions import db
from contest.init_defaults import initialize_defaults
from config import TestConfig


@pytest.fixture()
def app_fixture():
    app = create_app(TestConfig)
    return app

@pytest.fixture(scope='function')
def client(app_fixture):
    return app_fixture.test_client()

@pytest.fixture(scope='function', autouse=True)
def db_session(app_fixture):
    with app_fixture.app_context():
        db.create_all()
        initialize_defaults(app_fixture)  # Ajout ici
        yield db.session
        db.session.remove()

@pytest.fixture(scope='function', autouse=True)
def mock_stravalib_client():
    """
    Automatically mock stravalib.Client for all tests.
    """
    with patch("contest.tasks.Client") as mock_client:
        # Configure the mock as needed
        instance = mock_client.return_value

        # Mock get_athlete
        instance.get_athlete.return_value = MagicMock(
            id=123,
            firstname="Test",
            lastname="User",
            country="Testland"
        )

        # Mock get_activities to return a list of mock activities
        mock_activity = MagicMock()
        mock_activity.id = 1
        mock_activity.name = "Mock Activity"
        mock_activity.distance = 1000
        mock_activity.moving_time = 600
        mock_activity.elapsed_time = 650
        mock_activity.start_date = datetime(2025, 1, 1, 10, 0, 0)
        mock_activity.total_elevation_gain = 50
        mock_activity.type.root = "Run"
        instance.get_activities.return_value = [mock_activity]

        # Mock refresh_access_token
        instance.refresh_access_token.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": 9999999999
        }

        yield mock_client
