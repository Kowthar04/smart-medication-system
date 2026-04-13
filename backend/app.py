from flask import Flask, request, jsonify, render_template
import psycopg2
from datetime import datetime, time

app = Flask(__name__) 


def get_db_connection():
    conn = psycopg2.connect(
        dbname="smart_medication_db",
        user="kowtharabdiqadir",
        host="localhost",
    )
    return conn  


def run_query(query, params=(), fetchone=False, commit=False):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(query, params)

        result = None
        if commit:
            conn.commit()
        elif fetchone:
            result = cur.fetchone()
        else:
            result = cur.fetchall()

        return result
    finally:
        cur.close()
        conn.close()


def format_time_value(value):
    if value is None:
        return "--:--"

    if isinstance(value, str):
        return value[:5]

    return value.strftime("%H:%M")


def parse_time_value(value):
    if value is None:
        return None

    if isinstance(value, time):
        return value

    if isinstance(value, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue

    return None


def get_schedule_data():
    rows = run_query(
        """
        SELECT medication_name, scheduled_time, dose
        FROM medication_schedules
        ORDER BY scheduled_time ASC
        """
    )

    schedule = []
    for row in rows:
        raw_time = row[1]
        schedule.append({
            "name": row[0],
            "time": format_time_value(raw_time),
            "time_obj": parse_time_value(raw_time),
            "dose": row[2]
        })

    return schedule


def get_last_event():
    row = run_query(
        """
        SELECT event_type, event_time, container_id, weight_change
        FROM medication_events
        ORDER BY id DESC
        LIMIT 1
        """,
        fetchone=True
    )

    if not row:
        return None

    raw_time = row[1]

    return {
        "event_type": row[0],
        "event_time": format_time_value(raw_time),
        "event_time_obj": parse_time_value(raw_time),
        "container_id": row[2],
        "weight_change": row[3]
    }


def get_recent_events(limit=10):
    rows = run_query(
        """
        SELECT event_type, event_time, created_at
        FROM medication_events
        WHERE DATE(created_at) = CURRENT_DATE
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,)
    )

    recent_events = []
    for row in rows:
        raw_event_time = row[1]
        raw_created_at = row[2]

        recent_events.append({
            "event_type": row[0],
            "event_time": format_time_value(raw_event_time),
            "event_time_obj": parse_time_value(raw_event_time),
            "created_at": raw_created_at
        })

    return recent_events


def build_schedule_map(schedule):
    schedule_map = {}
    for item in schedule:
        if item["time_obj"] is not None:
            schedule_map[item["time_obj"]] = item
    return schedule_map


def get_last_taken(recent_events, schedule):
    taken_events = [event for event in recent_events if event["event_type"] == "taken"]

    if not taken_events:
        return {
            "name": "No medication recorded",
            "time": "--:--",
            "dose": "--",
            "status": "No data",
            "badge_class": "neutral"
        }

    latest_taken = taken_events[0]
    event_time_obj = latest_taken["event_time_obj"]
    event_time = latest_taken["event_time"]

    matched_medication = None
    for med in schedule:
        if med["time_obj"] == event_time_obj:
            matched_medication = med
            break

    if matched_medication:
        return {
            "name": matched_medication["name"],
            "time": event_time,
            "dose": matched_medication["dose"],
            "status": "On time",
            "badge_class": "success"
        }

    earlier_medication = None
    for med in schedule:
        if med["time_obj"] and event_time_obj and med["time_obj"] < event_time_obj:
            earlier_medication = med

    if earlier_medication:
        return {
            "name": earlier_medication["name"],
            "time": event_time,
            "dose": earlier_medication["dose"],
            "status": "Late",
            "badge_class": "warning"
        }

    first_med = schedule[0] if schedule else None
    if first_med:
        return {
            "name": first_med["name"],
            "time": event_time,
            "dose": first_med["dose"],
            "status": "Too early",
            "badge_class": "warning"
        }

    return {
        "name": "Unknown medication",
        "time": event_time,
        "dose": "--",
        "status": "No match",
        "badge_class": "neutral"
    }


def build_recent_activity(recent_events, schedule):
    activity = []

    for event in recent_events:
        event_type = event["event_type"]
        event_time = event["event_time"]
        event_time_obj = event["event_time_obj"]

        matched_medication = None
        earlier_medication = None
        later_medication = None

        for med in schedule:
            if med["time_obj"] == event_time_obj:
                matched_medication = med
                break

        for med in schedule:
            if med["time_obj"] and event_time_obj:
                if med["time_obj"] < event_time_obj:
                    earlier_medication = med
                if med["time_obj"] > event_time_obj and later_medication is None:
                    later_medication = med

        if event_type == "taken" and matched_medication:
            message = f"{matched_medication['name']} taken at scheduled time"
            activity_type = "on-time"

        elif event_type == "taken" and earlier_medication:
            message = f"{earlier_medication['name']} taken late"
            activity_type = "late"

        elif event_type == "taken" and later_medication:
            message = f"{later_medication['name']} taken too early"
            activity_type = "early"

        elif event_type == "suspicious":
            message = "Suspicious event - dosage too high"
            activity_type = "suspicious"

        elif event_type == "new_medication":
            message = "New medication assigned"
            activity_type = "new"

        else:
            message = f"{event_type} recorded at {event_time}"
            activity_type = "default"

        activity.append({
            "message": message,
            "time": event_time,
            "type": activity_type
        })

    return activity


def get_adherence_data(last_taken):
    if last_taken["status"] == "On time":
        return 100, f"{last_taken['name']} dose taken on time"

    if last_taken["status"] == "Late":
        return 0, "Latest dose was taken late"

    if last_taken["status"] == "Too early":
        return 0, "Latest dose was taken too early"

    return 0, "No dose recorded"

def get_next_due(schedule, recent_events):
    taken_events = [event for event in recent_events if event["event_type"] == "taken"]

    if not schedule:
        return {
            "name": "No more doses today",
            "time": "--:--",
            "dose": "--"
        }

    if not taken_events:
        return {
            "name": schedule[0]["name"],
            "time": schedule[0]["time"],
            "dose": schedule[0]["dose"]
        }

    latest_taken = taken_events[0]
    event_time_obj = latest_taken["event_time_obj"]

    for med in schedule:
        if med["time_obj"] and event_time_obj and med["time_obj"] > event_time_obj:
            return {
                "name": med["name"],
                "time": med["time"],
                "dose": med["dose"]
            }

    return {
        "name": "No more doses today",
        "time": "--:--",
        "dose": "--"
    }

def build_schedule_with_status(schedule, recent_events):
    taken_times = set()

    for event in recent_events:
        if event["event_type"] == "taken" and event["event_time_obj"] is not None:
            taken_times.add(event["event_time_obj"])

    updated_schedule = []

    taken_found = False

    for item in schedule:
        if item["time_obj"] in taken_times:
            status = "Taken"
            tag_class = "taken"
            taken_found = True
        elif not taken_found:
            status = "Missed"
            tag_class = "missed"
        else:
            status = "Upcoming"
            tag_class = "upcoming"

        updated_schedule.append({
            "name": item["name"],
            "time": item["time"],
            "dose": item["dose"],
            "status": status,
            "tag_class": tag_class
        })

    return updated_schedule


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/event", methods=["POST"])
def receive_event():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "event" not in data or "time" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    event_type = data["event"]
    event_time = data["time"]
    container_id = data.get("container_id", "default_container")
    weight_change = data.get("weight_change")

    run_query(
        """
        INSERT INTO medication_events (event_type, event_time, container_id, weight_change)
        VALUES (%s, %s, %s, %s)
        """,
        (event_type, event_time, container_id, weight_change),
        commit=True
    )

    return jsonify({"status": "event received"})


@app.route("/events", methods=["GET"])
def get_events():
    rows = run_query(
        """
        SELECT id, event_type, event_time, container_id, weight_change
        FROM medication_events
        ORDER BY id DESC
        """
    )

    events = []
    for row in rows:
        events.append({
            "id": row[0],
            "event": row[1],
            "time": format_time_value(row[2]),
            "container_id": row[3],
            "weight_change": row[4],
        })

    return jsonify(events)


@app.route("/schedule", methods=["GET"])
def get_schedule():
    schedule = get_schedule_data()

    clean_schedule = []
    for item in schedule:
        clean_schedule.append({
            "name": item["name"],
            "time": item["time"],
            "dose": item["dose"]
        })

    return jsonify(clean_schedule)


@app.route("/adherence", methods=["GET"])
def check_adherence():
    schedule = get_schedule_data()

    if not schedule:
        return jsonify({"error": "No medication schedule found"}), 404

    first_medication = schedule[0]
    scheduled_time_obj = first_medication["time_obj"]

    row = run_query(
        """
        SELECT event_time
        FROM medication_events
        WHERE event_time = %s
        LIMIT 1
        """,
        (scheduled_time_obj,),
        fetchone=True
    )

    if row:
        return jsonify({
            "medication": first_medication["name"],
            "scheduled_time": first_medication["time"],
            "status": "taken on time",
        })

    return jsonify({
        "medication": first_medication["name"],
        "scheduled_time": first_medication["time"],
        "status": "missed",
    })


@app.route("/patient/dashboard", methods=["GET"])
def patient_dashboard():
    schedule = get_schedule_data()
    recent_events = get_recent_events()

    last_taken = get_last_taken(recent_events, schedule)
    recent_activity = build_recent_activity(recent_events, schedule)
    adherence_rate, adherence_note = get_adherence_data(last_taken)
    next_due = get_next_due(schedule, recent_events)
    schedule_with_status = build_schedule_with_status(schedule, recent_events)

    clean_schedule = []
    for item in schedule:
        clean_schedule.append({
            "name": item["name"],
            "time": item["time"],
            "dose": item["dose"]
        })

    dashboard_data = {
    "last_taken": last_taken,
    "next_due": next_due,
    "adherence_rate": adherence_rate,
    "adherence_note": adherence_note,
    "recent_activity": recent_activity,
    "schedule": schedule_with_status
}

    return render_template("patient_dashboard.html", dashboard_data=dashboard_data)

@app.route("/patient/schedule", methods=["GET"])
def patient_schedule():
    schedule = get_schedule_data()
    recent_events = get_recent_events()

    schedule_with_status = build_schedule_with_status(schedule, recent_events)
    next_due = get_next_due(schedule, recent_events)

    medications = ["All Medications"]
    for item in schedule:
        if item["name"] not in medications:
            medications.append(item["name"])

    schedule_data = {
        "schedule": schedule_with_status,
        "next_due": next_due,
        "medications": medications
    }

    return render_template("patient_schedule.html", schedule_data=schedule_data)


@app.route("/wellbeing", methods=["POST"])
def save_wellbeing():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        mood = data.get("mood")
        energy = data.get("energy")
        side_effects = data.get("side_effects")

        if not mood or not energy or not side_effects:
            return jsonify({"error": "Missing wellbeing fields"}), 400

        run_query(
            """
            INSERT INTO wellbeing_checkins (mood, energy, side_effects)
            VALUES (%s, %s, %s)
            """,
            (mood, energy, side_effects),
            commit=True
        )

        return jsonify({"status": "saved"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)
