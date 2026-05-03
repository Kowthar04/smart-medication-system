import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, abort
import psycopg2
from datetime import datetime, time, timedelta

from auth import auth_bp, login_required, role_required


app = Flask(__name__)

app.secret_key = os.environ.get(
    "MEDITRACK_SECRET_KEY",
    "dev-only-not-for-production-replace-this-via-env",
)
app.register_blueprint(auth_bp)



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



def get_active_patient_id():
    """Return the patient_id the current request should operate on.

    For patients: their own patient_id.
    For caregivers/doctors: whichever patient they've selected via the
    picker (session["viewing_patient_id"]). If they haven't picked one
    yet, we default to the first patient assigned to them.

    Returns None if the user is somehow logged in but unable to resolve
    a patient (e.g. a caregiver with no assignments yet).
    """
    role = session.get("role")

    if role == "patient":
        return session.get("patient_id")

    if role in ("caregiver", "doctor"):
        viewing = session.get("viewing_patient_id")
        if viewing:
            return viewing

       
        assigned = list_assigned_patients(session["user_id"], role)
        if assigned:
            first_id = assigned[0]["patient_id"]
            session["viewing_patient_id"] = first_id
            return first_id
        return None

    return None


def list_assigned_patients(user_id, role):
    """Return [{patient_id, full_name}] for caregiver/doctor user_id."""
    if role == "caregiver":
        join_table = "caregiver_patient"
        join_col = "caregiver_id"
    elif role == "doctor":
        join_table = "doctor_patient"
        join_col = "doctor_id"
    else:
        return []

    rows = run_query(
        f"""
        SELECT p.id, u.full_name
        FROM {join_table} jt
        JOIN patients p ON p.id = jt.patient_id
        JOIN users    u ON u.id = p.user_id
        WHERE jt.{join_col} = %s
        ORDER BY u.full_name ASC
        """,
        (user_id,),
    )

    return [{"patient_id": row[0], "full_name": row[1]} for row in rows]


def get_patient_display_name(patient_id):
    """Return the patient's full_name, or 'Unknown' if no row."""
    if patient_id is None:
        return "Unknown"
    row = run_query(
        """
        SELECT u.full_name
        FROM patients p
        JOIN users    u ON u.id = p.user_id
        WHERE p.id = %s
        """,
        (patient_id,),
        fetchone=True,
    )
    return row[0] if row else "Unknown"


def assert_caregiver_can_view(caregiver_user_id, patient_id):
    """Verify the caregiver is actually assigned to this patient.

    Defends against URL tampering — without this, a caregiver could
    set viewing_patient_id to any number via cookie editing and see
    other patients' data.
    """
    row = run_query(
        """
        SELECT 1
        FROM caregiver_patient
        WHERE caregiver_id = %s AND patient_id = %s
        """,
        (caregiver_user_id, patient_id),
        fetchone=True,
    )
    return row is not None


def assert_doctor_can_view(doctor_user_id, patient_id):
    """Same as above for doctors."""
    row = run_query(
        """
        SELECT 1
        FROM doctor_patient
        WHERE doctor_id = %s AND patient_id = %s
        """,
        (doctor_user_id, patient_id),
        fetchone=True,
    )
    return row is not None




def get_schedule_data(patient_id):
    rows = run_query(
        """
        SELECT medication_name, scheduled_time, dose
        FROM medication_schedules
        WHERE patient_id = %s
        ORDER BY scheduled_time ASC
        """,
        (patient_id,),
    )
    schedule = []
    for row in rows:
        raw_time = row[1]
        schedule.append({
            "name": row[0],
            "time": format_time_value(raw_time),
            "time_obj": parse_time_value(raw_time),
            "dose": row[2],
        })
    return schedule


def get_recent_events(patient_id, limit=200):
    rows = run_query(
        """
        SELECT event_type, event_time, created_at
        FROM medication_events
        WHERE patient_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (patient_id, limit),
    )
    events = []
    for row in rows:
        events.append({
            "event_type": row[0],
            "event_time": format_time_value(row[1]),
            "event_time_obj": parse_time_value(row[1]),
            "created_at": row[2],
        })
    return events


def get_last_taken(recent_events, schedule):
    taken_events = [e for e in recent_events if e["event_type"] == "taken"]
    if not taken_events:
        return {
            "name": "No medication recorded",
            "time": "--:--",
            "dose": "--",
            "status": "No data",
            "badge_class": "neutral",
        }

    latest_taken = taken_events[0]
    event_time_obj = latest_taken["event_time_obj"]
    event_time = latest_taken["event_time"]

    matched = next(
        (m for m in schedule if m["time_obj"] == event_time_obj), None
    )
    if matched:
        return {
            "name": matched["name"],
            "time": event_time,
            "dose": matched["dose"],
            "status": "On time",
            "badge_class": "success",
        }

    earlier = None
    for med in schedule:
        if med["time_obj"] and event_time_obj and med["time_obj"] < event_time_obj:
            earlier = med
    if earlier:
        return {
            "name": earlier["name"],
            "time": event_time,
            "dose": earlier["dose"],
            "status": "Late",
            "badge_class": "warning",
        }

    if schedule:
        first = schedule[0]
        return {
            "name": first["name"],
            "time": event_time,
            "dose": first["dose"],
            "status": "Too early",
            "badge_class": "warning",
        }

    return {
        "name": "Unknown medication",
        "time": event_time,
        "dose": "--",
        "status": "No match",
        "badge_class": "neutral",
    }


def build_recent_activity(recent_events, schedule):
    activity = []
    for event in recent_events:
        event_type = event["event_type"]
        event_time = event["event_time"]
        event_time_obj = event["event_time_obj"]

        matched = next(
            (m for m in schedule if m["time_obj"] == event_time_obj), None
        )
        earlier = None
        later = None
        for med in schedule:
            if med["time_obj"] and event_time_obj:
                if med["time_obj"] < event_time_obj:
                    earlier = med
                if med["time_obj"] > event_time_obj and later is None:
                    later = med

        if event_type == "taken" and matched:
            message = f"{matched['name']} taken at scheduled time"
            activity_type = "on-time"
        elif event_type == "taken" and earlier:
            message = f"{earlier['name']} taken late"
            activity_type = "late"
        elif event_type == "taken" and later:
            message = f"{later['name']} taken too early"
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
            "type": activity_type,
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
    taken_events = [e for e in recent_events if e["event_type"] == "taken"]
    if not schedule:
        return {"name": "No more doses today", "time": "--:--", "dose": "--"}
    if not taken_events:
        return {
            "name": schedule[0]["name"],
            "time": schedule[0]["time"],
            "dose": schedule[0]["dose"],
        }

    latest_taken = taken_events[0]
    event_time_obj = latest_taken["event_time_obj"]
    for med in schedule:
        if med["time_obj"] and event_time_obj and med["time_obj"] > event_time_obj:
            return {"name": med["name"], "time": med["time"], "dose": med["dose"]}

    return {"name": "No more doses today", "time": "--:--", "dose": "--"}


def build_schedule_with_status(schedule, recent_events):
    taken_times = {
        e["event_time_obj"]
        for e in recent_events
        if e["event_type"] == "taken" and e["event_time_obj"] is not None
    }

    updated = []
    for item in schedule:
        if item["time_obj"] in taken_times:
            status, tag_class = "Taken", "taken"
        else:
            status, tag_class = "Upcoming", "upcoming"
        updated.append({
            "name": item["name"],
            "time": item["time"],
            "dose": item["dose"],
            "status": status,
            "tag_class": tag_class,
        })
    return updated



def calculate_current_streak(patient_id):
    """Consecutive days where every scheduled dose for this patient was taken."""
    schedule = get_schedule_data(patient_id)
    if not schedule:
        return 0

    rows = run_query(
        """
        SELECT event_time, created_at::date AS day
        FROM medication_events
        WHERE patient_id = %s AND event_type = 'taken'
        """,
        (patient_id,),
    )

    taken_by_day = set()
    for row in rows:
        t = parse_time_value(row[0])
        d = row[1]
        if t is not None and d is not None:
            taken_by_day.add((d, t))

    today = datetime.now().date()
    streak = 0
    cursor_day = today

    for _ in range(365):
        all_taken_today = all(
            (cursor_day, m["time_obj"]) in taken_by_day for m in schedule
        )
        if not all_taken_today:
            
            if cursor_day == today:
                cursor_day -= timedelta(days=1)
                continue
            break
        streak += 1
        cursor_day -= timedelta(days=1)

    return streak


def compute_morning_vs_evening_insight(patient_id):
    """Return an insight dict, or None if there isn't enough data yet."""
    schedule = get_schedule_data(patient_id)
    if not schedule:
        return None

    morning_meds = [m for m in schedule if m["time_obj"] and m["time_obj"].hour < 12]
    evening_meds = [m for m in schedule if m["time_obj"] and m["time_obj"].hour >= 17]
    if not morning_meds or not evening_meds:
        return None

    rows = run_query(
        """
        SELECT event_time
        FROM medication_events
        WHERE patient_id = %s
          AND event_type = 'taken'
          AND created_at >= NOW() - INTERVAL '14 days'
        """,
        (patient_id,),
    )
    if len(rows) < 7:
        return None

    morning_times = {m["time_obj"] for m in morning_meds}
    evening_times = {m["time_obj"] for m in evening_meds}

    morning_taken = sum(1 for r in rows if parse_time_value(r[0]) in morning_times)
    evening_taken = sum(1 for r in rows if parse_time_value(r[0]) in evening_times)

    morning_total = len(morning_meds) * 14
    evening_total = len(evening_meds) * 14

    morning_pct = round((morning_taken / morning_total) * 100) if morning_total else 0
    evening_pct = round((evening_taken / evening_total) * 100) if evening_total else 0

    if morning_pct - evening_pct >= 15:
        return {
            "label": "PATTERN DETECTED",
            "headline": "You're most consistent with morning doses",
            "body": (f"Mornings sit at {morning_pct}% but evenings are at "
                     f"{evening_pct}%. Try setting a reminder around your "
                     "evening routine."),
        }
    if evening_pct - morning_pct >= 15:
        return {
            "label": "PATTERN DETECTED",
            "headline": "Evenings are your strongest window",
            "body": (f"Evenings sit at {evening_pct}% but mornings drop to "
                     f"{morning_pct}%. A bedtime alarm or morning prompt "
                     "could close the gap."),
        }
    if morning_pct >= 90 and evening_pct >= 90:
        return {
            "label": "GREAT WORK",
            "headline": "Strong adherence across the day",
            "body": (f"Both morning ({morning_pct}%) and evening "
                     f"({evening_pct}%) doses are well above target. "
                     "Keep it up."),
        }
    return None


def compute_14_day_trend(patient_id):
    """Returns SVG polyline points + delta vs prior 14 days, or None."""
    schedule = get_schedule_data(patient_id)
    if not schedule:
        return None

    today = datetime.now().date()
    window_days = 14

    rows = run_query(
        """
        SELECT event_time, created_at::date AS day
        FROM medication_events
        WHERE patient_id = %s
          AND event_type = 'taken'
          AND created_at >= %s
        """,
        (patient_id, today - timedelta(days=window_days * 2 - 1)),
    )
    if len(rows) < 3:
        return None

    taken = set()
    for row in rows:
        t = parse_time_value(row[0])
        d = row[1]
        if t is not None and d is not None:
            taken.add((d, t))

    doses_per_day = len(schedule)
    if doses_per_day == 0:
        return None

    daily_pct = []
    for offset in range(window_days - 1, -1, -1):
        day = today - timedelta(days=offset)
        taken_today = sum(
            1 for med in schedule if (day, med["time_obj"]) in taken
        )
        daily_pct.append(round((taken_today / doses_per_day) * 100))

    prior = []
    for offset in range(window_days * 2 - 1, window_days - 1, -1):
        day = today - timedelta(days=offset)
        taken_today = sum(
            1 for med in schedule if (day, med["time_obj"]) in taken
        )
        prior.append(round((taken_today / doses_per_day) * 100))

    current_avg = sum(daily_pct) / len(daily_pct)
    prior_avg = sum(prior) / len(prior) if prior else 0
    delta = round(current_avg - prior_avg)

    if delta > 0:
        delta_class = "up"
    elif delta < 0:
        delta_class = "down"
    else:
        delta_class = "flat"

    width, height = 260, 90
    points = []
    last_index = max(len(daily_pct) - 1, 1)
    for i, pct in enumerate(daily_pct):
        x = round((i / last_index) * width)
        y = round(height - (pct / 100) * (height - 10) - 5)
        points.append(f"{x},{y}")

    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    return {
        "points": " ".join(points),
        "delta_pct": delta,
        "delta_class": delta_class,
        "delta_label": f"{arrow} {abs(delta)}%",
    }


def compute_medication_breakdown_insight(medication_breakdown):
    """Pick the most interesting per-medication insight, or None."""
    if not medication_breakdown or len(medication_breakdown) < 2:
        return None
    sorted_meds = sorted(medication_breakdown, key=lambda m: m["percentage"], reverse=True)
    best, worst = sorted_meds[0], sorted_meds[-1]
    if best["percentage"] - worst["percentage"] < 20:
        return None
    if worst["percentage"] < 50:
        return {
            "label": "NEEDS ATTENTION",
            "headline": f"{worst['name']} is your weakest routine",
            "body": (f"{worst['name']} is at {worst['percentage']}% while "
                     f"{best['name']} sits at {best['percentage']}%. "
                     "Consider pairing it with a daily habit you already keep."),
        }
    return {
        "label": "INSIGHT",
        "headline": f"{best['name']} is your strongest routine",
        "body": (f"{best['name']} is at {best['percentage']}%, leading "
                 f"{worst['name']} at {worst['percentage']}%."),
    }


def compute_day_stats(schedule_with_status):
    """Day stat counters — pulled out from inside the dedup loop bug."""
    taken = upcoming = late = 0
    for item in schedule_with_status:
        if item["tag_class"] == "taken":
            taken += 1
        elif item["tag_class"] == "upcoming":
            upcoming += 1
        elif item["tag_class"] == "late":
            late += 1
    return {
        "taken": taken,
        "upcoming": upcoming,
        "late": late,
        "total": len(schedule_with_status),
    }


def get_recent_notes(patient_id, limit=20):
    rows = run_query(
        """
        SELECT n.id, n.note_text, n.tag, n.related_time, n.created_at, u.full_name
        FROM caregiver_notes n
        JOIN users u ON u.id = n.author_id
        WHERE n.patient_id = %s
        ORDER BY n.created_at DESC
        LIMIT %s
        """,
        (patient_id, limit),
    )
    notes = []
    for row in rows:
        notes.append({
            "id": row[0],
            "text": row[1],
            "tag": row[2],
            "related_time": format_time_value(row[3]) if row[3] else None,
            "created_at": row[4],
            "author_name": row[5],
        })
    return notes


def build_month_calendar():
    today = datetime.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    days_in_month = (next_month - first_day).days
    start_offset = first_day.weekday()

    calendar_days = []
    for _ in range(start_offset):
        calendar_days.append({"day": "", "is_empty": True, "is_today": False, "dot_class": ""})

    for day in range(1, days_in_month + 1):
        current_date = first_day.replace(day=day)
        if current_date < today:
            dot_class = "taken-dot"
        elif current_date == today:
            dot_class = "today-dot"
        else:
            dot_class = ""
        calendar_days.append({
            "day": day,
            "is_empty": False,
            "is_today": current_date == today,
            "dot_class": dot_class,
        })

    return {"month_name": today.strftime("%B %Y"), "days": calendar_days}



def calculate_adherence_today(schedule, recent_events, medication_filter):
    today = datetime.now().date()
    result = {}
    for item in schedule:
        name = item["name"]
        if medication_filter != "all" and name != medication_filter:
            continue
        if name not in result:
            result[name] = {"taken": 0, "total": 0}
        result[name]["total"] += 1
        for event in recent_events:
            if (
                event["event_type"] == "taken"
                and event["event_time_obj"] == item["time_obj"]
                and event["created_at"].date() == today
            ):
                result[name]["taken"] += 1
                break

    labels, data = [], []
    for name, vals in result.items():
        pct = round((vals["taken"] / vals["total"]) * 100) if vals["total"] else 0
        labels.append(name)
        data.append(pct)
    return labels, data


def calculate_adherence_weekly(schedule, recent_events, medication_filter):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    result = {}
    for item in schedule:
        name = item["name"]
        if medication_filter != "all" and name != medication_filter:
            continue
        if name not in result:
            result[name] = {"taken": 0, "total": 0}
        result[name]["total"] += 7
        for event in recent_events:
            if event["event_type"] != "taken":
                continue
            if event["event_time_obj"] != item["time_obj"]:
                continue
            event_date = event["created_at"].date()
            if start_of_week <= event_date <= end_of_week:
                result[name]["taken"] += 1
    labels, data = [], []
    for name, vals in result.items():
        pct = round((vals["taken"] / vals["total"]) * 100) if vals["total"] else 0
        labels.append(name)
        data.append(pct)
    return labels, data


def calculate_adherence_monthly(schedule, recent_events, medication_filter):
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    days_in_month = (next_month - start_of_month).days

    result = {}
    for item in schedule:
        name = item["name"]
        if medication_filter != "all" and name != medication_filter:
            continue
        if name not in result:
            result[name] = {"taken": 0, "total": 0}
        result[name]["total"] += days_in_month
        for event in recent_events:
            if event["event_type"] != "taken":
                continue
            if event["event_time_obj"] != item["time_obj"]:
                continue
            event_date = event["created_at"].date()
            if start_of_month <= event_date < next_month:
                result[name]["taken"] += 1
    labels, data = [], []
    for name, vals in result.items():
        pct = round((vals["taken"] / vals["total"]) * 100) if vals["total"] else 0
        labels.append(name)
        data.append(pct)
    return labels, data




@app.route("/", methods=["GET"])
def root_redirect():
    """Default landing — bounce to login or each role's dashboard."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    role = session.get("role")
    if role == "patient":
        return redirect(url_for("patient_dashboard"))
    if role == "caregiver":
        return redirect(url_for("caregiver_dashboard"))
    if role == "doctor":
        return redirect(url_for("auth.doctor_placeholder"))
    return redirect(url_for("auth.login"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})



@app.route("/event", methods=["POST"])
def receive_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "event" not in data or "time" not in data or "patient_id" not in data:
        return jsonify({"error": "Missing required fields (event, time, patient_id)"}), 400

    event_type = data["event"]
    event_time = data["time"]
    patient_id = data["patient_id"]
    container_id = data.get("container_id", "default_container")
    weight_change = data.get("weight_change")

    run_query(
        """
        INSERT INTO medication_events
            (patient_id, event_type, event_time, container_id, weight_change)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (patient_id, event_type, event_time, container_id, weight_change),
        commit=True,
    )

    return jsonify({"status": "event received"})



@app.route("/log-dose", methods=["POST"])
@login_required
def log_dose():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    scheduled_time = data.get("time")
    if not scheduled_time:
        return jsonify({"error": "Missing dose time"}), 400

    patient_id = get_active_patient_id()
    if patient_id is None:
        return jsonify({"error": "No patient context"}), 400

    
    if session.get("role") == "caregiver":
        if not assert_caregiver_can_view(session["user_id"], patient_id):
            abort(403)

    actual_time = datetime.now().time().replace(microsecond=0)
    source = data.get("source", "manual_dashboard")
    container_label = f"{source}:{scheduled_time}"

    run_query(
        """
        INSERT INTO medication_events
            (patient_id, event_type, event_time, container_id, weight_change)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (patient_id, "taken", actual_time, container_label, None),
        commit=True,
    )
    return jsonify({
        "status": "logged",
        "message": "Dose marked as taken",
        "logged_at": actual_time.strftime("%H:%M"),
    })



# patient dashboard
@app.route("/patient/dashboard", methods=["GET"])
@role_required("patient")
def patient_dashboard():
    patient_id = session["patient_id"]

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)

    last_taken = get_last_taken(recent_events, schedule)
    recent_activity = build_recent_activity(recent_events, schedule)
    adherence_rate, adherence_note = get_adherence_data(last_taken)
    next_due = get_next_due(schedule, recent_events)
    schedule_with_status = build_schedule_with_status(schedule, recent_events)

    streak = calculate_current_streak(patient_id)
    insight = compute_morning_vs_evening_insight(patient_id)
    trend = compute_14_day_trend(patient_id)

    dashboard_data = {
        "last_taken": last_taken,
        "next_due": next_due,
        "adherence_rate": adherence_rate,
        "adherence_note": adherence_note,
        "recent_activity": recent_activity,
        "schedule": schedule_with_status,
        "patient_name": session.get("full_name", "Patient"),
        "streak": streak,
        "insight": insight,
        "trend": trend,
    }
    return render_template("patient_dashboard.html", dashboard_data=dashboard_data)


@app.route("/patient/schedule", methods=["GET"])
@role_required("patient")
def patient_schedule():
    patient_id = session["patient_id"]
    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)

    schedule_with_status = build_schedule_with_status(schedule, recent_events)

    medications = []
    for item in schedule_with_status:
        if item["name"] not in medications:
            medications.append(item["name"])

    schedule_data = {
        "schedule": schedule_with_status,
        "medications": medications,
        "calendar": build_month_calendar(),
        "day_stats": compute_day_stats(schedule_with_status),
    }
    return render_template("patient_schedule.html", schedule_data=schedule_data)


@app.route("/patient/adherence", methods=["GET"])
@role_required("patient")
def patient_adherence():
    patient_id = session["patient_id"]
    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id, limit=200)

    medications = [item["name"] for item in schedule]

    total_doses = len(schedule)
    taken_times = {
        e["event_time_obj"]
        for e in recent_events
        if e["event_type"] == "taken" and e["event_time_obj"] is not None
    }
    taken_doses = sum(1 for item in schedule if item["time_obj"] in taken_times)
    missed_doses = total_doses - taken_doses
    overall_adherence = round((taken_doses / total_doses) * 100) if total_doses else 0

    summary = {
        "overall_adherence": overall_adherence,
        "doses_taken": f"{taken_doses} / {total_doses}",
        "missed_doses": missed_doses,
    }

    breakdown_labels, breakdown_values = calculate_adherence_today(
        schedule, recent_events, "all"
    )
    medication_breakdown = [
        {"name": label, "percentage": breakdown_values[i]}
        for i, label in enumerate(breakdown_labels)
    ]
    insight = compute_medication_breakdown_insight(medication_breakdown)

    return render_template(
        "patient_adherence.html",
        medications=medications,
        summary=summary,
        medication_breakdown=medication_breakdown,
        insight=insight,
    )



# adherence data
@app.route("/adherence-data", methods=["GET"])
@login_required
def adherence_data():
    period = request.args.get("period", "daily")
    medication = request.args.get("medication", "all")

    patient_id = get_active_patient_id()
    if patient_id is None:
        return jsonify({"labels": [], "data": []})

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id, limit=200)

    if period == "weekly":
        labels, data = calculate_adherence_weekly(schedule, recent_events, medication)
    elif period == "monthly":
        labels, data = calculate_adherence_monthly(schedule, recent_events, medication)
    else:
        labels, data = calculate_adherence_today(schedule, recent_events, medication)

    return jsonify({"labels": labels, "data": data})



# patient wellbeing check in
@app.route("/wellbeing", methods=["POST"])
@role_required("patient")
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

        patient_id = session["patient_id"]
        run_query(
            """
            INSERT INTO wellbeing_checkins
                (patient_id, mood, energy, side_effects)
            VALUES (%s, %s, %s, %s)
            """,
            (patient_id, mood, energy, side_effects),
            commit=True,
        )
        return jsonify({"status": "saved"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# note saving
@app.route("/save-note", methods=["POST"])
@role_required("caregiver", "doctor")
def save_note():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        note_text = (data.get("note_text") or "").strip()
        tag = data.get("tag")
        related_time = data.get("related_time")
        if not note_text:
            return jsonify({"error": "Note cannot be empty"}), 400

        if tag and tag not in ("Mood", "Pain", "Side effect", "Appetite", "Sleep"):
            tag = None

        related_time_obj = parse_time_value(related_time) if related_time else None

        patient_id = get_active_patient_id()
        if patient_id is None:
            return jsonify({"error": "No patient context"}), 400

        if session["role"] == "caregiver":
            if not assert_caregiver_can_view(session["user_id"], patient_id):
                abort(403)
        elif session["role"] == "doctor":
            if not assert_doctor_can_view(session["user_id"], patient_id):
                abort(403)

        run_query(
            """
            INSERT INTO caregiver_notes
                (patient_id, author_id, note_text, tag, related_time)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (patient_id, session["user_id"], note_text, tag, related_time_obj),
            commit=True,
        )
        return jsonify({"status": "saved"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# patient picker
@app.route("/caregiver/select-patient/<int:patient_id>", methods=["POST", "GET"])
@role_required("caregiver", "doctor")
def caregiver_select_patient(patient_id):
    role = session["role"]
    if role == "caregiver":
        ok = assert_caregiver_can_view(session["user_id"], patient_id)
    else:
        ok = assert_doctor_can_view(session["user_id"], patient_id)

    if not ok:
        abort(403)

    session["viewing_patient_id"] = patient_id
    referrer = request.referrer
    if referrer and url_for("caregiver_dashboard") in referrer:
        return redirect(referrer)
    return redirect(url_for("caregiver_dashboard"))



# Caregiver pages
def _caregiver_context():
    """Common context for every caregiver page (picker state + name)."""
    user_id = session["user_id"]
    role = session["role"]
    assigned = list_assigned_patients(user_id, role)
    active_patient_id = get_active_patient_id()
    active_patient_name = get_patient_display_name(active_patient_id) if active_patient_id else None
    return {
        "assigned_patients": assigned,
        "active_patient_id": active_patient_id,
        "active_patient_name": active_patient_name,
        "caregiver_name": session.get("full_name", "Caregiver"),
    }


@app.route("/caregiver/dashboard", methods=["GET"])
@role_required("caregiver")
def caregiver_dashboard():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]

    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)
    schedule_with_status = build_schedule_with_status(schedule, recent_events)
    activity = build_recent_activity(recent_events, schedule)
    notes = get_recent_notes(patient_id, limit=10)

    return render_template(
        "caregiver_dashboard.html",
        ctx=ctx,
        schedule=schedule_with_status,
        activity=activity,
        notes=notes,
    )


@app.route("/caregiver/schedule", methods=["GET"])
@role_required("caregiver")
def caregiver_schedule():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]
    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)
    schedule_with_status = build_schedule_with_status(schedule, recent_events)
    medications = list(dict.fromkeys(item["name"] for item in schedule_with_status))

    schedule_data = {
        "schedule": schedule_with_status,
        "medications": medications,
        "calendar": build_month_calendar(),
        "day_stats": compute_day_stats(schedule_with_status),
    }
    return render_template(
        "caregiver_schedule.html",
        ctx=ctx,
        schedule_data=schedule_data,
    )


@app.route("/caregiver/adherence", methods=["GET"])
@role_required("caregiver")
def caregiver_adherence():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]
    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id, limit=200)

    medications = [item["name"] for item in schedule]
    total_doses = len(schedule)
    taken_times = {
        e["event_time_obj"]
        for e in recent_events
        if e["event_type"] == "taken" and e["event_time_obj"] is not None
    }
    taken_doses = sum(1 for item in schedule if item["time_obj"] in taken_times)
    missed_doses = total_doses - taken_doses
    overall = round((taken_doses / total_doses) * 100) if total_doses else 0

    summary = {
        "overall_adherence": overall,
        "doses_taken": f"{taken_doses} / {total_doses}",
        "missed_doses": missed_doses,
    }

    labels, values = calculate_adherence_today(schedule, recent_events, "all")
    medication_breakdown = [
        {"name": labels[i], "percentage": values[i]} for i in range(len(labels))
    ]
    insight = compute_medication_breakdown_insight(medication_breakdown)

    return render_template(
        "caregiver_adherence.html",
        ctx=ctx,
        medications=medications,
        summary=summary,
        medication_breakdown=medication_breakdown,
        insight=insight,
    )


@app.route("/caregiver/notes", methods=["GET"])
@role_required("caregiver")
def caregiver_notes_page():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]
    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)
    schedule_with_status = build_schedule_with_status(schedule, recent_events)
    notes = get_recent_notes(patient_id, limit=50)

    return render_template(
        "caregiver_notes.html",
        ctx=ctx,
        notes=notes,
        schedule=schedule_with_status,
    )


@app.route("/caregiver/alerts", methods=["GET"])
@role_required("caregiver")
def caregiver_alerts():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]
    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)
    activity = build_recent_activity(recent_events, schedule)

    severity = {
        "suspicious": 0,
        "late": 1,
        "early": 2,
        "default": 3,
        "on-time": 4,
        "new": 5,
    }
    alerts = sorted(activity, key=lambda a: severity.get(a["type"], 99))

    return render_template("caregiver_alerts.html", ctx=ctx, alerts=alerts)



@app.route("/patient/care-team", methods=["GET"])
@role_required("patient")
def patient_care_team():
    return render_template("patient_care_team.html")


@app.route("/patient/settings", methods=["GET"])
@role_required("patient")
def patient_settings():
    return render_template("patient_settings.html")


if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)