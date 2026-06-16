import importlib

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def client():
    """Reload the application module before each test to reset in-memory state."""
    importlib.reload(app_module)
    return TestClient(app_module.app)


def test_root_redirects_to_static_index_html(client):
    # Arrange
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert expected_activity in activities
    assert activities[expected_activity]["max_participants"] == 12
    assert "michael@mergington.edu" in activities[expected_activity]["participants"]


def test_signup_for_activity_adds_new_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    activity_response = client.get("/activities")
    participants = activity_response.json()[activity_name]["participants"]
    assert email in participants


def test_signup_for_activity_returns_400_when_participant_already_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "existingstudent@mergington.edu"
    first_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert first_response.status_code == 200

    # Act
    duplicate_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up"


def test_unregister_participant_removes_existing_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    activity_response = client.get("/activities")
    assert email not in activity_response.json()[activity_name]["participants"]


def test_unregister_participant_returns_404_for_unknown_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "missingstudent@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unregister_participant_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
