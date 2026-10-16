import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, g, jsonify, request
from flask_cors import CORS
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


app = Flask(__name__)
CORS(app)

HTTP_REQUESTS_TOTAL = Counter(
    "campus_http_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "campus_http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"]
)

EVENT_REGISTRATIONS_TOTAL = Counter(
    "campus_event_registrations_total",
    "Total number of successful event registrations"
)

APP_NAME = os.getenv(
    "APP_NAME",
    "Campus Event Management System"
)

APP_ENV = os.getenv(
    "APP_ENV",
    "DEVELOPMENT"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0-dev"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "DEBUG"
)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/app/data/campus_events.db"
)

ALLOWED_CATEGORIES = [
    "Technical",
    "Workshop",
    "Seminar",
    "Cultural",
    "Sports",
    "Placement",
    "Other"
]

ALLOWED_STATUSES = [
    "active",
    "completed",
    "cancelled"
]

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def get_database_connection():
    database_file = Path(DATABASE_PATH)

    database_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        database_file
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database():
    connection = get_database_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            event_date TEXT NOT NULL,
            venue TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_code TEXT UNIQUE,
            event_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            registered_at TEXT NOT NULL,
            FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE
        )
        """
    )

    event_count = connection.execute(
        "SELECT COUNT(*) AS total FROM events"
    ).fetchone()["total"]

    if event_count == 0:
        sample_events = [
            (
                "DevOps and Cloud Bootcamp",
                "Practical workshop covering Git, Docker, "
                "Terraform and cloud deployment.",
                "Workshop",
                "2026-09-18",
                "Computer Engineering Lab",
                40,
                "active",
                datetime.now().isoformat()
            ),
            (
                "AI Innovation Hackathon",
                "A campus hackathon for developing "
                "innovative AI-based solutions.",
                "Technical",
                "2026-09-24",
                "Innovation Centre",
                60,
                "active",
                datetime.now().isoformat()
            ),
            (
                "Placement Readiness Seminar",
                "Resume preparation, aptitude guidance "
                "and interview preparation.",
                "Placement",
                "2026-10-03",
                "Seminar Hall",
                100,
                "active",
                datetime.now().isoformat()
            )
        ]

        connection.executemany(
            """
            INSERT INTO events (
                title,
                description,
                category,
                event_date,
                venue,
                capacity,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_events
        )

    connection.commit()
    connection.close()


def convert_event_to_dictionary(
    connection,
    event
):
    registration_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM registrations
        WHERE event_id = ?
        AND status = 'active'
        """,
        (event["id"],)
    ).fetchone()["total"]

    event_data = dict(event)

    event_data["registered_count"] = (
        registration_count
    )

    event_data["available_seats"] = max(
        event["capacity"] - registration_count,
        0
    )

    return event_data


def validate_event_data(data):
    errors = {}

    required_fields = [
        "title",
        "description",
        "category",
        "event_date",
        "venue",
        "capacity"
    ]

    for field in required_fields:
        if not data.get(field):
            errors[field] = (
                f"{field.replace('_', ' ').title()} "
                "is required."
            )

    if data.get("category") not in ALLOWED_CATEGORIES:
        errors["category"] = (
            "Select a valid event category."
        )

    try:
        capacity = int(data.get("capacity", 0))

        if capacity <= 0:
            errors["capacity"] = (
                "Capacity must be greater than zero."
            )

    except (TypeError, ValueError):
        errors["capacity"] = (
            "Capacity must be a valid number."
        )

    try:
        datetime.strptime(
            data.get("event_date", ""),
            "%Y-%m-%d"
        )

    except ValueError:
        errors["event_date"] = (
            "Event date must use YYYY-MM-DD format."
        )

    return errors


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_request_metrics(response):
    if request.path != "/metrics":
        endpoint = (
            request.url_rule.rule
            if request.url_rule is not None
            else "unknown"
        )

        duration = (
            time.perf_counter()
            - getattr(g, "request_start_time", time.perf_counter())
        )

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code)
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

    return response


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


@app.route("/", methods=["GET"])
def root():
    return jsonify(
        message="Campus Event API is running",
        environment=APP_ENV,
        version=APP_VERSION
    )


@app.route("/health", methods=["GET"])
def health():
    try:
        connection = get_database_connection()

        connection.execute(
            "SELECT 1"
        ).fetchone()

        connection.close()

        return jsonify(
            status="healthy",
            application=APP_NAME,
            service="campus-event-backend",
            environment=APP_ENV,
            version=APP_VERSION,
            database="connected"
        )

    except sqlite3.Error:
        return jsonify(
            status="unhealthy",
            database="disconnected"
        ), 503


@app.route("/api/info", methods=["GET"])
def get_application_information():
    return jsonify(
        application=APP_NAME,
        environment=APP_ENV,
        version=APP_VERSION,
        log_level=LOG_LEVEL,
        deployment="Docker and Terraform"
    )


@app.route("/api/events", methods=["GET"])
def get_events():
    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    query = "SELECT * FROM events WHERE 1 = 1"

    parameters = []

    if search:
        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
                OR venue LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    if category:
        query += " AND category = ?"
        parameters.append(category)

    if status:
        query += " AND status = ?"
        parameters.append(status)

    query += " ORDER BY event_date ASC"

    connection = get_database_connection()

    events = connection.execute(
        query,
        parameters
    ).fetchall()

    event_list = [
        convert_event_to_dictionary(
            connection,
            event
        )
        for event in events
    ]

    connection.close()

    return jsonify(event_list)


@app.route(
    "/api/events/<int:event_id>",
    methods=["GET"]
)
def get_event(event_id):
    connection = get_database_connection()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if event is None:
        connection.close()

        return jsonify(
            error="Event not found."
        ), 404

    event_data = convert_event_to_dictionary(
        connection,
        event
    )

    connection.close()

    return jsonify(event_data)


@app.route("/api/events", methods=["POST"])
def create_event():
    data = request.get_json(
        silent=True
    ) or {}

    errors = validate_event_data(data)

    if errors:
        return jsonify(
            error="Validation failed.",
            fields=errors
        ), 400

    status = data.get(
        "status",
        "active"
    )

    if status not in ALLOWED_STATUSES:
        status = "active"

    connection = get_database_connection()

    cursor = connection.execute(
        """
        INSERT INTO events (
            title,
            description,
            category,
            event_date,
            venue,
            capacity,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["title"].strip(),
            data["description"].strip(),
            data["category"],
            data["event_date"],
            data["venue"].strip(),
            int(data["capacity"]),
            status,
            datetime.now().isoformat()
        )
    )

    connection.commit()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?",
        (cursor.lastrowid,)
    ).fetchone()

    event_data = convert_event_to_dictionary(
        connection,
        event
    )

    connection.close()

    return jsonify(event_data), 201


@app.route(
    "/api/events/<int:event_id>",
    methods=["PUT"]
)
def update_event(event_id):
    data = request.get_json(
        silent=True
    ) or {}

    errors = validate_event_data(data)

    if errors:
        return jsonify(
            error="Validation failed.",
            fields=errors
        ), 400

    status = data.get(
        "status",
        "active"
    )

    if status not in ALLOWED_STATUSES:
        return jsonify(
            error="Invalid event status."
        ), 400

    connection = get_database_connection()

    existing_event = connection.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if existing_event is None:
        connection.close()

        return jsonify(
            error="Event not found."
        ), 404

    registration_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM registrations
        WHERE event_id = ?
        AND status = 'active'
        """,
        (event_id,)
    ).fetchone()["total"]

    if int(data["capacity"]) < registration_count:
        connection.close()

        return jsonify(
            error=(
                "Capacity cannot be less than the "
                "current registration count."
            )
        ), 409

    connection.execute(
        """
        UPDATE events
        SET
            title = ?,
            description = ?,
            category = ?,
            event_date = ?,
            venue = ?,
            capacity = ?,
            status = ?
        WHERE id = ?
        """,
        (
            data["title"].strip(),
            data["description"].strip(),
            data["category"],
            data["event_date"],
            data["venue"].strip(),
            int(data["capacity"]),
            status,
            event_id
        )
    )

    connection.commit()

    updated_event = connection.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    event_data = convert_event_to_dictionary(
        connection,
        updated_event
    )

    connection.close()

    return jsonify(event_data)


@app.route(
    "/api/events/<int:event_id>",
    methods=["DELETE"]
)
def delete_event(event_id):
    connection = get_database_connection()

    event = connection.execute(
        "SELECT id FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if event is None:
        connection.close()

        return jsonify(
            error="Event not found."
        ), 404

    connection.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )

    connection.commit()
    connection.close()

    return jsonify(
        message="Event deleted successfully."
    )


@app.route(
    "/api/events/<int:event_id>/register",
    methods=["POST"]
)
def register_for_event(event_id):
    data = request.get_json(
        silent=True
    ) or {}

    student_name = data.get(
        "student_name",
        ""
    ).strip()

    roll_number = data.get(
        "roll_number",
        ""
    ).strip().upper()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    if len(student_name) < 2:
        return jsonify(
            error="Enter a valid student name."
        ), 400

    if len(roll_number) < 2:
        return jsonify(
            error="Enter a valid roll number."
        ), 400

    if not EMAIL_PATTERN.match(email):
        return jsonify(
            error="Enter a valid email address."
        ), 400

    connection = get_database_connection()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if event is None:
        connection.close()

        return jsonify(
            error="Event not found."
        ), 404

    if event["status"] != "active":
        connection.close()

        return jsonify(
            error="Registration is closed."
        ), 409

    registration_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM registrations
        WHERE event_id = ?
        AND status = 'active'
        """,
        (event_id,)
    ).fetchone()["total"]

    if registration_count >= event["capacity"]:
        connection.close()

        return jsonify(
            error="No seats are available."
        ), 409

    duplicate = connection.execute(
        """
        SELECT id
        FROM registrations
        WHERE event_id = ?
        AND roll_number = ?
        AND status = 'active'
        """,
        (
            event_id,
            roll_number
        )
    ).fetchone()

    if duplicate is not None:
        connection.close()

        return jsonify(
            error=(
                "This roll number is already "
                "registered for the event."
            )
        ), 409

    cursor = connection.execute(
        """
        INSERT INTO registrations (
            registration_code,
            event_id,
            student_name,
            roll_number,
            email,
            status,
            registered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            None,
            event_id,
            student_name,
            roll_number,
            email,
            "active",
            datetime.now().isoformat()
        )
    )

    registration_code = (
        f"REG-{event_id:03d}-"
        f"{cursor.lastrowid:05d}"
    )

    connection.execute(
        """
        UPDATE registrations
        SET registration_code = ?
        WHERE id = ?
        """,
        (
            registration_code,
            cursor.lastrowid
        )
    )

    connection.commit()

    registration = connection.execute(
        """
        SELECT
            registrations.*,
            events.title AS event_title,
            events.event_date,
            events.venue
        FROM registrations
        JOIN events
            ON events.id = registrations.event_id
        WHERE registrations.id = ?
        """,
        (cursor.lastrowid,)
    ).fetchone()

    connection.close()

    EVENT_REGISTRATIONS_TOTAL.inc()

    return jsonify(
        dict(registration)
    ), 201


@app.route(
    "/api/registrations",
    methods=["GET"]
)
def get_registrations():
    roll_number = request.args.get(
        "roll_number",
        ""
    ).strip().upper()

    query = """
        SELECT
            registrations.*,
            events.title AS event_title,
            events.event_date,
            events.venue
        FROM registrations
        JOIN events
            ON events.id = registrations.event_id
        WHERE 1 = 1
    """

    parameters = []

    if roll_number:
        query += (
            " AND registrations.roll_number = ?"
        )

        parameters.append(roll_number)

    query += (
        " ORDER BY "
        "registrations.registered_at DESC"
    )

    connection = get_database_connection()

    registrations = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return jsonify([
        dict(registration)
        for registration in registrations
    ])


@app.route(
    "/api/registrations/<registration_code>",
    methods=["DELETE"]
)
def cancel_registration(registration_code):
    connection = get_database_connection()

    registration = connection.execute(
        """
        SELECT *
        FROM registrations
        WHERE registration_code = ?
        """,
        (registration_code.upper(),)
    ).fetchone()

    if registration is None:
        connection.close()

        return jsonify(
            error="Registration not found."
        ), 404

    if registration["status"] == "cancelled":
        connection.close()

        return jsonify(
            error="Registration is already cancelled."
        ), 409

    connection.execute(
        """
        UPDATE registrations
        SET status = 'cancelled'
        WHERE id = ?
        """,
        (registration["id"],)
    )

    connection.commit()
    connection.close()

    return jsonify(
        message="Registration cancelled successfully.",
        registration_code=registration_code.upper()
    )


initialize_database()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )