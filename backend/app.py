from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__) 

medication_schedule = { # hardcoded testing data
    "name": "Vitamin D",
    "time": "12:00",
}
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
    return jsonify(medication_schedule) # shows the scheduled data for meds
@app.route("/adherence", methods=["GET"])
def check_adherence(): # checks if the medication was taken on time compared to scheduled time
    scheduled_time = medication_schedule["time"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT event_time FROM medication_events WHERE event_time = %s", (scheduled_time,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({
            "medication": medication_schedule["name"],
            "scheduled_time": scheduled_time,
            "status": "taken on time",
        }) # is returned if event matches the scheduled time and function ends
    return jsonify({
        "medication": medication_schedule["name"],
        "scheduled_time": scheduled_time,
        "status": "missed",
    }) # is returned if no event matches the scheduled time

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)

    # By running python3 app.py, the flask server starts and it creates an empty events list and the waits for incoming requests. The /health endpoint can be used to check if the server is running, and it will return {"status": "ok"}. The /event endpoint can be used to send medication events, which will be stored in the events list. The /adherence endpoint checks if there is an event that matches the scheduled medication time and returns whether the medication was taken on time or missed.

