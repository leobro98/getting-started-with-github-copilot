"""Tests for the FastAPI application endpoints"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Basketball Team": {
            "description": "Join the school basketball team and compete in local leagues",
            "schedule": "Mondays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Drama Society": {
            "description": "Participate in acting, stage production, and school plays",
            "schedule": "Fridays, 4:00 PM - 6:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Math Olympiad": {
            "description": "Prepare for math competitions and solve challenging problems",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 14,
            "participants": []
        },
        "Soccer Club": {
            "description": "Practice soccer skills and play friendly matches",
            "schedule": "Wednesdays, 3:30 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        }
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Clean up after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # We have 9 activities
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant lists"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        
        # Art Club should have no participants
        assert len(data["Art Club"]["participants"]) == 0


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Art Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up test@mergington.edu for Art Club"
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Art Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client):
        """Test that signing up twice returns error"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Student is already signed up for this activity"
    
    def test_signup_with_url_encoded_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # Chess Club has michael@mergington.edu
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Removed michael@mergington.edu from Chess Club"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_remove_participant_nonexistent_activity(self, client):
        """Test removing participant from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_remove_participant_not_enrolled(self, client):
        """Test removing participant who is not enrolled returns 404"""
        response = client.delete(
            "/activities/Art Club/participants/notregistered@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Participant not found in this activity"
    
    def test_remove_participant_with_url_encoded_email(self, client):
        """Test removal with URL-encoded email address"""
        # First add a participant with special characters
        email = "test+special@mergington.edu"
        client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        
        # Now remove using URL encoding
        response = client.delete(
            f"/activities/Art%20Club/participants/{email}"
        )
        
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""
    
    def test_complete_signup_and_removal_workflow(self, client):
        """Test a complete workflow: view activities, sign up, then remove"""
        # 1. Get initial activities
        response = client.get("/activities")
        assert response.status_code == 200
        initial_data = response.json()
        initial_count = len(initial_data["Math Olympiad"]["participants"])
        
        # 2. Sign up for an activity
        email = "workflow@mergington.edu"
        signup_response = client.post(
            "/activities/Math Olympiad/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # 3. Verify participant was added
        after_signup = client.get("/activities")
        after_signup_data = after_signup.json()
        assert len(after_signup_data["Math Olympiad"]["participants"]) == initial_count + 1
        assert email in after_signup_data["Math Olympiad"]["participants"]
        
        # 4. Remove the participant
        remove_response = client.delete(
            f"/activities/Math Olympiad/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # 5. Verify participant was removed
        after_removal = client.get("/activities")
        after_removal_data = after_removal.json()
        assert len(after_removal_data["Math Olympiad"]["participants"]) == initial_count
        assert email not in after_removal_data["Math Olympiad"]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test that a user can sign up for multiple different activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Art Club", "Chess Club", "Soccer Club"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify user is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
