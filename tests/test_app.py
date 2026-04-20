import copy

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_activity_name():
    return "Chess Club"


@pytest.fixture
def sample_email():
    return "test_student@example.com"


class TestGetActivities:
    def test_get_activities_returns_expected_structure(self, client):
        # Arrange
        expected_status = 200

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == expected_status
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert isinstance(data["Chess Club"]["participants"], list)

    def test_get_activities_contains_required_fields(self, client):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity_data in activities_data.items():
            for field in required_fields:
                assert field in activity_data


class TestSignupForActivity:
    def test_signup_new_student_succeeds(self, client, sample_activity_name, sample_email):
        # Arrange
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[sample_activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": sample_email},
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

        updated_response = client.get("/activities")
        updated_activity = updated_response.json()[sample_activity_name]
        assert len(updated_activity["participants"]) == initial_count + 1
        assert sample_email in updated_activity["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client, sample_email):
        # Arrange
        nonexistent_activity = "Nonexistent Activity"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": sample_email},
        )

        # Assert
        assert response.status_code == 404
        assert "activity not found" in response.json()["detail"].lower()

    def test_signup_duplicate_returns_400(self, client, sample_activity_name):
        # Arrange
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": existing_email},
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    def test_unregister_existing_student_succeeds(self, client, sample_activity_name, sample_email):
        # Arrange
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": sample_email},
        )
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[sample_activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": sample_email},
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

        updated_response = client.get("/activities")
        updated_activity = updated_response.json()[sample_activity_name]
        assert len(updated_activity["participants"]) == initial_count - 1
        assert sample_email not in updated_activity["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client, sample_email):
        # Arrange
        nonexistent_activity = "Nonexistent Activity"

        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": sample_email},
        )

        # Assert
        assert response.status_code == 404
        assert "activity not found" in response.json()["detail"].lower()

    def test_unregister_missing_participant_returns_400(self, client, sample_activity_name):
        # Arrange
        missing_email = "missing_student@example.com"

        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": missing_email},
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
