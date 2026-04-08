from flask import Flask, request, jsonify, render_template
import psycopg2

app = Flask(__name__) 


def get_db_connection():
    conn = psycopg2.connect(
        dbname="smart_medication_db",
        user="kowtharabdiqadir",
        host="localhost",
    )
    return conn

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}) #checks if the server is still running

@app.route("/event", methods=["POST"])
def receive_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "time" not in data or "event" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    event_type = data["event"]
    event_time = data["time"]
    container_id = data.get("container_id", "default_container")
    weight_change = data.get("weight_change", None)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO medication_events (event_type, event_time, container_id, weight_change) 
        VALUES (%s, %s, %s, %s)
        """,
        (event_type, event_time, container_id, weight_change))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "event received"}) # receives the medication event data and stores it in the database, then returns a confirmation message


@app.route("/events", methods=["GET"])
def get_events():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, event_type, event_time, container_id, weight_change FROM medication_events")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    events = []
    for row in rows:
        events.append({
            "id": row[0],
            "event": row[1],
            "time": row[2],
            "container_id": row[3],
            "weight_change": row[4],
        })
    return jsonify(events) # returns the full list of events

@app.route("/schedule", methods=["GET"])
def get_schedule():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT medication_name, scheduled_time, dose
        FROM medication_schedules
        ORDER BY scheduled_time ASC
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    schedule = []
    for row in rows:
        schedule.append({
            "name": row[0],
            "time": row[1],
            "dose": row[2]
        })

    return jsonify(schedule)

@app.route("/adherence", methods=["GET"])
def check_adherence():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT medication_name, scheduled_time, dose
        FROM medication_schedules
        ORDER BY scheduled_time ASC
        LIMIT 1
    """)
    medication_row = cur.fetchone()

    if not medication_row:
        cur.close()
        conn.close()
        return jsonify({"error": "No medication schedule found"}), 404

    medication_name = medication_row[0]
    scheduled_time = medication_row[1]

    cur.execute("""
        SELECT event_time
        FROM medication_events
        WHERE event_time = %s
        LIMIT 1
    """, (scheduled_time,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return jsonify({
            "medication": medication_name,
            "scheduled_time": scheduled_time,
            "status": "taken on time",
        })

    return jsonify({
        "medication": medication_name,
        "scheduled_time": scheduled_time,
        "status": "missed",
    })

@app.route("/patient/dashboard", methods=["GET"])
def patient_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # get full medication schedule from database
    cur.execute("""
        SELECT medication_name, scheduled_time, dose
        FROM medication_schedules
        ORDER BY scheduled_time ASC
    """)
    schedule_rows = cur.fetchall()

    schedule = []
    for row in schedule_rows:
        schedule.append({
            "name": row[0],
            "time": row[1],
            "dose": row[2]
        })

    # latest medication event
    cur.execute("""
        SELECT event_type, event_time, container_id, weight_change
        FROM medication_events
        ORDER BY id DESC
        LIMIT 1
    """)
    last_event = cur.fetchone()

    # latest 4 events for Recent Activity
    cur.execute("""
        SELECT event_type, event_time
        FROM medication_events
        ORDER BY id DESC
        LIMIT 4
    """)
    recent_rows = cur.fetchall()

    cur.close()
    conn.close()

    # find medication matching the latest event time
    matched_medication = None
    if last_event:
        event_time = last_event[1]
        for med in schedule:
            if med["time"] == event_time:
                matched_medication = med
                break

    # latest medication status
    if last_event and matched_medication:
        last_taken = {
            "name": matched_medication["name"],
            "time": last_event[1],
            "dose": matched_medication["dose"],
            "status": "On time"
        }
    elif last_event:
        # if no exact match, try to infer nearest earlier medication as late
        event_time = last_event[1]
        earlier_medication = None

        for med in schedule:
            if med["time"] < event_time:
                earlier_medication = med

        if earlier_medication:
            last_taken = {
                "name": earlier_medication["name"],
                "time": event_time,
                "dose": earlier_medication["dose"],
                "status": "Late"
            }
        else:
            last_taken = {
                "name": "Unknown medication",
                "time": event_time,
                "dose": "--",
                "status": "No match"
            }
    else:
        last_taken = {
            "name": "No medication recorded",
            "time": "--:--",
            "dose": "--",
            "status": "No data"
        }

    # recent activity list
    recent_activity = []
    for row in recent_rows:
        event_type = row[0]
        event_time = row[1]

        matched_activity_med = None
        for med in schedule:
            if med["time"] == event_time:
                matched_activity_med = med
                break

        if event_type == "taken" and matched_activity_med:
            message = f"{matched_activity_med['name']} taken at scheduled time"
            activity_type = "on-time"

        elif event_type == "taken" and not matched_activity_med:
            earlier_medication = None
            later_medication = None

            for med in schedule:
                if med["time"] > event_time and later_medication is None:
                    later_medication = med

            for med in schedule:
                if med["time"] < event_time:
                    earlier_medication = med

            if earlier_medication:
                message = f"{earlier_medication['name']} taken late"
                activity_type = "late"
            elif later_medication:
                message = f"{later_medication['name']} taken too early"
                activity_type = "early"
            else:
                message = f"Medication event recorded at {event_time}"
                activity_type = "default"

        elif event_type == "suspicious":
            message = "Suspicious event - dosage too high"
            activity_type = "suspicious"

        elif event_type == "new_medication":
            message = "New medication assigned"
            activity_type = "new"

        else:
            message = f"{event_type} recorded at {event_time}"
            activity_type = "default"

        recent_activity.append({
            "message": message,
            "time": event_time,
            "type": activity_type
        })

    # adherence based on latest event
    if last_event and matched_medication:
        adherence_rate = 100
        adherence_note = f"{matched_medication['name']} dose taken on time"
    elif last_event:
        adherence_rate = 0
        adherence_note = "Latest dose was taken late"
    else:
        adherence_rate = 0
        adherence_note = "No dose recorded"

        # next due logic
    next_due = None

    if last_event:
        event_time = last_event[1]

        # find next medication after current time
        for med in schedule:
            if med["time"] > event_time:
                next_due = med
                break

    else:
        next_due = schedule[0]

    # fallback cases
    if not next_due:
        next_due = {
            "name": "No more doses today",
            "time": "--:--",
            "dose": "--"
        }

    dashboard_data = {
        "last_taken": last_taken,
        "next_due": next_due,
        "adherence_rate": adherence_rate,
        "adherence_note": adherence_note,
        "recent_activity": recent_activity,
        "schedule": schedule
    }

    return render_template("patient_dashboard.html", dashboard_data=dashboard_data)

@app.route("/wellbeing", methods=["POST"])
def save_wellbeing():
    try:
        data = request.get_json()
        print("WELLBEING DATA RECEIVED:", data)

        mood = data.get("mood")
        energy = data.get("energy")
        side_effects = data.get("side_effects")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO wellbeing_checkins (mood, energy, side_effects)
            VALUES (%s, %s, %s)
        """, (mood, energy, side_effects))

        conn.commit()
        cur.close()
        conn.close()

        print("WELLBEING SAVED SUCCESSFULLY")
        return jsonify({"status": "saved"})
    
    except Exception as e:
        print("WELLBEING ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)

    # By running python3 app.py, the flask server starts and it creates an empty events list and the waits for incoming requests. The /health endpoint can be used to check if the server is running, and it will return {"status": "ok"}. The /event endpoint can be used to send medication events, which will be stored in the events list. The /adherence endpoint checks if there is an event that matches the scheduled medication time and returns whether the medication was taken on time or missed.

