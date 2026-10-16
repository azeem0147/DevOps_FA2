import os
import sys
import tempfile
from pathlib import Path

import pytest


TEST_DIRECTORY = tempfile.TemporaryDirectory()
TEST_DATABASE = Path(TEST_DIRECTORY.name) / "test_campus_events.db"

os.environ["DATABASE_PATH"] = str(TEST_DATABASE)
os.environ["APP_ENV"] = "TEST"
os.environ["APP_VERSION"] = "2.0.0-test"
os.environ["LOG_LEVEL"] = "DEBUG"

BACKEND_DIRECTORY = Path(__file__).resolve().parent

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

import app as backend_app


@pytest.fixture(autouse=True)
def reset_test_database():
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()

    backend_app.initialize_database()

    yield

    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


@pytest.fixture
def client():
    backend_app.app.config.update(TESTING=True)
    return backend_app.app.test_client()


def test_health_endpoint_returns_healthy_status(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["environment"] == "TEST"


def test_application_information_endpoint(client):
    response = client.get("/api/info")

    assert response.status_code == 200

    data = response.get_json()

    assert data["application"] == "Campus Event Management System"
    assert data["environment"] == "TEST"
    assert data["version"] == "2.0.0-test"


def test_event_listing_returns_sample_events(client):
    response = client.get("/api/events")

    assert response.status_code == 200

    events = response.get_json()

    assert isinstance(events, list)
    assert len(events) >= 3
    assert "title" in events[0]
    assert "available_seats" in events[0]


def test_invalid_event_is_rejected(client):
    response = client.post(
        "/api/events",
        json={
            "title": "",
            "description": "",
            "category": "Invalid Category",
            "event_date": "invalid-date",
            "venue": "",
            "capacity": 0
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Validation failed."
    assert "fields" in data


def test_valid_event_can_be_created(client):
    response = client.post(
        "/api/events",
        json={
            "title": "FA2 Kubernetes Workshop",
            "description": (
                "Workshop covering CI/CD, Kubernetes, "
                "Prometheus and Grafana."
            ),
            "category": "Workshop",
            "event_date": "2026-11-10",
            "venue": "DevOps Laboratory",
            "capacity": 50,
            "status": "active"
        }
    )

    assert response.status_code == 201

    event = response.get_json()

    assert event["title"] == "FA2 Kubernetes Workshop"
    assert event["capacity"] == 50
    assert event["available_seats"] == 50


def test_duplicate_registration_is_rejected(client):
    registration = {
        "student_name": "Test Student",
        "roll_number": "FA2001",
        "email": "test.student@example.com"
    }

    first_response = client.post(
        "/api/events/1/register",
        json=registration
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/events/1/register",
        json=registration
    )

    assert second_response.status_code == 409

    data = second_response.get_json()

    assert "already registered" in data["error"]


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/health")
    client.get("/api/events")

    response = client.get("/metrics")

    assert response.status_code == 200

    metrics_text = response.get_data(as_text=True)

    assert "campus_http_requests_total" in metrics_text
    assert "campus_http_request_duration_seconds" in metrics_text
    assert "campus_event_registrations_total" in metrics_text
