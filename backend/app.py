from flask import Flask, request, jsonify

app = Flask(__name__)
events = []
medication_schedule = {
    "name": "Vitamin D",
    "time": "12:00",
}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
@app.route("/event", methods=["POST"])
def receive_event():
    data = request.get_json()
    events.append(data)
    return jsonify({"message": "event received", "data": data}), 201
@app.route("/events", methods=["GET"])
def get_events():
    return jsonify(events)
@app.route("/schedule", methods=["GET"])
def get_schedule():
    return jsonify(medication_schedule)
@app.route("/adherence", methods=["GET"])
def check_adherence():
    scheduled_time = medication_schedule["time"]
    for event in events:
        if event.get("time") == scheduled_time:
            return jsonify({
                "medication": medication_schedule["name"],
                "scheduled_time": scheduled_time,
                "status": "taken on time",
            })

    return jsonify({
        "medication": medication_schedule["name"],
        "scheduled_time": scheduled_time,
        "status": "missed",
    })

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)