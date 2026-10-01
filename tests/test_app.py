from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert "michael@mergington.edu" in response.json()[expected_activity]["participants"]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student@mergington.edu"
    endpoint = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "already-signed-up@mergington.edu"
    activities[activity_name]["participants"].append(email)
    endpoint = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    endpoint = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(endpoint, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student@mergington.edu"
    activities[activity_name]["participants"].append(email)
    endpoint = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_returns_404_when_student_is_not_registered(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "not-registered@mergington.edu"
    endpoint = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    endpoint = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(endpoint, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"