import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, abort
import psycopg2
from datetime import datetime, date, time, timedelta

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
    picker (session["viewing_patient_id"]). If that's stale or missing,
    we re-pick the first assigned patient.
    """
    role = session.get("role")

    if role == "patient":
        return session.get("patient_id")

    if role in ("caregiver", "doctor"):
        assigned = list_assigned_patients(session["user_id"], role)
        assigned_ids = {p["patient_id"] for p in assigned}

        viewing = session.get("viewing_patient_id")

       
        if viewing and viewing in assigned_ids:
            return viewing

        
        if assigned:
            first_id = assigned[0]["patient_id"]
            session["viewing_patient_id"] = first_id
            return first_id

        
        session.pop("viewing_patient_id", None)
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
        SELECT event_type, event_time, created_at, container_id
        FROM medication_events
        WHERE patient_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (patient_id, limit),
    )
    events = []
    for row in rows:
       
        scheduled_time_obj = None
        container_id = row[3]
        if container_id and ":" in container_id:
            
            _, _, scheduled_part = container_id.partition(":")
            scheduled_time_obj = parse_time_value(scheduled_part)

        events.append({
            "event_type": row[0],
            "event_time": format_time_value(row[1]),
            "event_time_obj": parse_time_value(row[1]),
            "scheduled_time_obj": scheduled_time_obj,
            "created_at": row[2],
            "container_id": container_id,
        })
    return events


def _match_time(event):
    """Return the time to match this event against the schedule.

    Modern events (post AUTH-2A) have scheduled_time_obj set from
    container_id. Legacy rows fall back to event_time_obj.
    """
    return event.get("scheduled_time_obj") or event["event_time_obj"]


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
    match_time = _match_time(latest_taken)
    actual_time = latest_taken["event_time_obj"]
    event_time = latest_taken["event_time"]

    matched = next(
        (m for m in schedule if m["time_obj"] == match_time), None
    )
    if matched:
       
        status = "On time"
        badge = "success"
        if actual_time and match_time and actual_time > match_time:
            
            late_threshold = (
                datetime.combine(datetime.today(), match_time)
                + timedelta(minutes=30)
            ).time()
            if actual_time > late_threshold:
                status = "Late"
                badge = "warning"
        return {
            "name": matched["name"],
            "time": event_time,
            "dose": matched["dose"],
            "status": status,
            "badge_class": badge,
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
        match_time = _match_time(event)
        actual_time = event["event_time_obj"]

        matched = next(
            (m for m in schedule if m["time_obj"] == match_time), None
        )

        if event_type == "taken" and matched:
           
            status_label = "at scheduled time"
            activity_type = "on-time"
            if actual_time and match_time and actual_time > match_time:
                late_threshold = (
                    datetime.combine(datetime.today(), match_time)
                    + timedelta(minutes=30)
                ).time()
                if actual_time > late_threshold:
                    status_label = "taken late"
                    activity_type = "late"
            message = f"{matched['name']} {status_label}"

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


def get_adherence_data(schedule, recent_events):
    """Compute today's adherence as a percentage and a short note.

    A scheduled dose only counts as "adhered" if it was taken within
    30 minutes of the scheduled time. Late doses are excluded from the
    percentage (they're tracked separately via build_schedule_with_status).
    """
    if not schedule:
        return 0, "No medications scheduled"

    today = datetime.now().date()

    on_time_taken = 0
    for med in schedule:
        for e in recent_events:
            if e["event_type"] != "taken":
                continue
            if e["created_at"].date() != today:
                continue
            if _match_time(e) != med["time_obj"]:
                continue
            if _is_on_time(e, med["time_obj"]):
                on_time_taken += 1
                break

    total = len(schedule)
    pct = round((on_time_taken / total) * 100) if total else 0

    if on_time_taken == 0:
        note = "No on-time doses recorded today"
    elif on_time_taken == total:
        note = f"All {total} doses taken on time today"
    else:
        note = f"{on_time_taken} of {total} doses on time today"

    return pct, note


def get_next_due(schedule, recent_events):
    if not schedule:
        return {"name": "No more doses today", "time": "--:--", "dose": "--"}

    today = datetime.now().date()

   
    taken_today = set()
    for e in recent_events:
        if e["event_type"] != "taken":
            continue
        if e["created_at"].date() != today:
            continue
        match_time = _match_time(e)
        if match_time:
            taken_today.add(match_time)

    now = datetime.now().time()

   
    for med in schedule:
        if med["time_obj"] not in taken_today:
            return {
                "name": med["name"],
                "time": med["time"],
                "dose": med["dose"],
            }

    return {"name": "No more doses today", "time": "--:--", "dose": "--"}


def build_schedule_with_status(schedule, recent_events):
    """Tag each scheduled dose for today as taken / late / upcoming / missed.

    - Taken: dose was logged today, on time (within 30 min of scheduled).
    - Late: dose was logged today but more than 30 min after scheduled.
    - Upcoming: scheduled time hasn't passed yet, no dose recorded.
    - Missed: scheduled time has passed and no dose recorded.
    """
    today = datetime.now().date()
    now = datetime.now().time()

    
    taken_today = {}
    for e in recent_events:
        if e["event_type"] != "taken":
            continue
        if e["created_at"].date() != today:
            continue
        match_time = _match_time(e)
        if match_time is not None:
            taken_today[match_time] = e["event_time_obj"]

    updated = []
    for item in schedule:
        scheduled = item["time_obj"]

        if scheduled in taken_today:
            actual = taken_today[scheduled]
            late_threshold = (
                datetime.combine(datetime.today(), scheduled)
                + timedelta(minutes=30)
            ).time()
            if actual and actual > late_threshold:
                status, tag_class = "Late", "late"
            else:
                status, tag_class = "Taken", "taken"
        elif scheduled and scheduled < now:
            
            status, tag_class = "Missed", "missed"
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
        SELECT container_id, created_at::date AS day
        FROM medication_events
        WHERE patient_id = %s AND event_type = 'taken'
        """,
        (patient_id,),
    )

    taken_by_day = set()
    for row in rows:
        container_id = row[0] or ""
        d = row[1]
       
        if ":" in container_id:
            _, _, scheduled_part = container_id.partition(":")
            t = parse_time_value(scheduled_part)
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
        SELECT container_id
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

    def _scheduled_from_container(container_id):
        if not container_id or ":" not in container_id:
            return None
        _, _, scheduled_part = container_id.partition(":")
        return parse_time_value(scheduled_part)

    morning_taken = sum(1 for r in rows if _scheduled_from_container(r[0]) in morning_times)
    evening_taken = sum(1 for r in rows if _scheduled_from_container(r[0]) in evening_times)

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
        SELECT container_id, created_at::date AS day
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
        container_id = row[0] or ""
        d = row[1]
        if ":" in container_id:
            _, _, scheduled_part = container_id.partition(":")
            t = parse_time_value(scheduled_part)
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
    taken = upcoming = late = missed = 0
    for item in schedule_with_status:
        if item["tag_class"] == "taken":
            taken += 1
        elif item["tag_class"] == "upcoming":
            upcoming += 1
        elif item["tag_class"] == "late":
            late += 1
        elif item["tag_class"] == "missed":
            missed += 1
    return {
        "taken": taken,
        "upcoming": upcoming,
        "late": late,
        "missed": missed,
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



def _is_on_time(event, scheduled_time_obj, late_threshold_minutes=30):
    """Return True if this event was logged within `late_threshold_minutes`
    of the scheduled time. Late doses don't count toward adherence %."""
    actual = event["event_time_obj"]
    if actual is None or scheduled_time_obj is None:
        return False
    late_threshold = (
        datetime.combine(datetime.today(), scheduled_time_obj)
        + timedelta(minutes=late_threshold_minutes)
    ).time()
    return actual <= late_threshold


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
                and _match_time(event) == item["time_obj"]
                and event["created_at"].date() == today
                and _is_on_time(event, item["time_obj"])
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
            if _match_time(event) != item["time_obj"]:
                continue
            if not _is_on_time(event, item["time_obj"]):
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
            if _match_time(event) != item["time_obj"]:
                continue
            if not _is_on_time(event, item["time_obj"]):
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
        return redirect(url_for("auth.doctor_dashboard"))
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


@app.route("/patient/dashboard", methods=["GET"])
@role_required("patient")
def patient_dashboard():
    patient_id = session["patient_id"]

    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id)

    last_taken = get_last_taken(recent_events, schedule)
    recent_activity = build_recent_activity(recent_events, schedule)
    adherence_rate, adherence_note = get_adherence_data(schedule, recent_events)
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
    today = datetime.now().date()
    taken_doses = 0
    for item in schedule:
        for e in recent_events:
            if e["event_type"] != "taken":
                continue
            if e["created_at"].date() != today:
                continue
            if _match_time(e) != item["time_obj"]:
                continue
            if _is_on_time(e, item["time_obj"]):
                taken_doses += 1
                break
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

def _doctor_context():
    """Common context for doctor pages (picker state + doctor name)."""
    user_id = session["user_id"]
    assigned = list_assigned_patients(user_id, "doctor")
    active_patient_id = get_active_patient_id()
    active_patient_name = get_patient_display_name(active_patient_id) if active_patient_id else None
    return {
        "assigned_patients": assigned,
        "active_patient_id": active_patient_id,
        "active_patient_name": active_patient_name,
        "doctor_name": session.get("full_name", "Doctor"),
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
    today = datetime.now().date()
    taken_doses = 0
    for item in schedule:
        for e in recent_events:
            if e["event_type"] != "taken":
                continue
            if e["created_at"].date() != today:
                continue
            if _match_time(e) != item["time_obj"]:
                continue
            if _is_on_time(e, item["time_obj"]):
                taken_doses += 1
                break
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



ALERT_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _generate_missed_dose_alerts(patient_id, schedule, recent_events):
    """Today's scheduled doses where the time has passed >30 min ago and
    no record exists. One alert per missed scheduled time."""
    today = datetime.now().date()
    now = datetime.now().time()

    
    taken_today = set()
    for e in recent_events:
        if e["event_type"] != "taken":
            continue
        if e["created_at"].date() != today:
            continue
        m = _match_time(e)
        if m is not None:
            taken_today.add(m)

    alerts = []
    for med in schedule:
        scheduled = med["time_obj"]
        if scheduled is None or scheduled in taken_today:
            continue

        
        cutoff = (
            datetime.combine(datetime.today(), scheduled)
            + timedelta(minutes=30)
        ).time()
        if now <= cutoff:
            continue  

        alert_id = f"missed:{patient_id}:{scheduled.strftime('%H%M')}:{today.isoformat()}"
        alerts.append({
            "id": alert_id,
            "severity": "high",
            "type": "missed",
            "title": f"{med['name']} missed",
            "body": f"Scheduled for {med['time']} — no dose recorded.",
            "when": today.strftime("%d %b %Y") + f" · scheduled {med['time']}",
            "_sort_time": scheduled,
        })
    return alerts


def _generate_late_pattern_alerts(patient_id, schedule, recent_events):
    """A medication taken late on 3+ of the last 7 days = pattern."""
    today = datetime.now().date()
    week_start = today - timedelta(days=6)

    
    late_counts = {}
    for e in recent_events:
        if e["event_type"] != "taken":
            continue
        event_date = e["created_at"].date()
        if event_date < week_start or event_date > today:
            continue
        match_time = _match_time(e)
        if match_time is None:
            continue
        
        med = next((m for m in schedule if m["time_obj"] == match_time), None)
        if not med:
            continue
        # Was it late?
        if not _is_on_time(e, match_time):
            late_counts.setdefault(med["name"], set()).add(event_date)

    alerts = []
    for name, dates in late_counts.items():
        if len(dates) < 3:
            continue
        alert_id = f"late_pattern:{patient_id}:{name.lower().replace(' ', '_')}"
        alerts.append({
            "id": alert_id,
            "severity": "medium",
            "type": "late_pattern",
            "title": f"{name} consistently late",
            "body": f"Taken late on {len(dates)} of the last 7 days. "
                    "Worth checking if the timing or routine needs adjustment.",
            "when": "Last 7 days",
            "_sort_time": None,
        })
    return alerts


def _generate_suspicious_event_alerts(patient_id, recent_events):
    """Suspicious events from the IoT pillbox — dosage anomaly."""
    alerts = []
    for e in recent_events:
        if e["event_type"] != "suspicious":
            continue
        
        ts = e["created_at"]
        alert_id = f"suspicious:{patient_id}:{ts.isoformat()}"
        alerts.append({
            "id": alert_id,
            "severity": "high",
            "type": "suspicious",
            "title": "Unusual dosage detected",
            "body": "The pillbox recorded an unexpected weight change — "
                    "this may indicate a double dose or tampering.",
            "when": ts.strftime("%d %b %Y, %H:%M"),
            "_sort_time": None,
        })
    return alerts


def _generate_wellbeing_alerts(patient_id):
    """Patient logged 'Low'/'Very low' mood, or specific side effects, in last 24h."""
    rows = run_query(
        """
        SELECT id, mood, energy, side_effects, created_at
        FROM wellbeing_checkins
        WHERE patient_id = %s
          AND created_at >= NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
        """,
        (patient_id,),
    )

    concerning_moods = {"Low", "Very low"}
    concerning_energy = {"Low", "Very low"}
    concerning_side_effects = {"Nausea", "Dizziness", "Headache", "Fatigue"}

    alerts = []
    for row in rows:
        wid, mood, energy, side_effects, created_at = row
        problems = []
        if mood in concerning_moods:
            problems.append(f"mood reported as {mood.lower()}")
        if energy in concerning_energy:
            problems.append(f"energy reported as {energy.lower()}")
        if side_effects in concerning_side_effects:
            problems.append(f"side effect: {side_effects.lower()}")

        if not problems:
            continue

        alert_id = f"wellbeing:{patient_id}:{wid}"
        alerts.append({
            "id": alert_id,
            "severity": "medium",
            "type": "wellbeing",
            "title": "Wellbeing check-in flagged",
            "body": "Patient reported: " + ", ".join(problems) + ".",
            "when": created_at.strftime("%d %b %Y, %H:%M"),
            "_sort_time": None,
        })
    return alerts


def get_acknowledgements_for_patient(patient_id):
    """Return {alert_id: {by_name, at}} for all alerts already acknowledged."""
    rows = run_query(
        """
        SELECT a.alert_id, u.full_name, a.acknowledged_at
        FROM alert_acknowledgements a
        JOIN users u ON u.id = a.acknowledged_by
        WHERE a.patient_id = %s
        ORDER BY a.acknowledged_at DESC
        """,
        (patient_id,),
    )
    return {
        row[0]: {"by_name": row[1], "at": row[2]}
        for row in rows
    }


def generate_alerts_for_patient(patient_id):
    """Run all alert generators and merge with acknowledgement data.

    Returns a dict with three buckets: needs_attention, worth_reviewing,
    acknowledged. Each alert is annotated with .acknowledgement if known.
    """
    schedule = get_schedule_data(patient_id)
    recent_events = get_recent_events(patient_id, limit=500)

    raw_alerts = []
    raw_alerts.extend(_generate_missed_dose_alerts(patient_id, schedule, recent_events))
    raw_alerts.extend(_generate_late_pattern_alerts(patient_id, schedule, recent_events))
    raw_alerts.extend(_generate_suspicious_event_alerts(patient_id, recent_events))
    raw_alerts.extend(_generate_wellbeing_alerts(patient_id))

   
    raw_alerts.sort(key=lambda a: (
        ALERT_SEVERITY_RANK.get(a["severity"], 99),
        a.get("_sort_time") or datetime.min.time(),
    ))

    acks = get_acknowledgements_for_patient(patient_id)

    needs_attention = []
    worth_reviewing = []
    acknowledged = []

    for alert in raw_alerts:
        if alert["id"] in acks:
            alert["acknowledgement"] = acks[alert["id"]]
            acknowledged.append(alert)
        elif alert["severity"] == "high":
            needs_attention.append(alert)
        else:
            worth_reviewing.append(alert)

    return {
        "needs_attention": needs_attention,
        "worth_reviewing": worth_reviewing,
        "acknowledged": acknowledged,
        "counts": {
            "high_unacked": len(needs_attention),
            "medium_unacked": len(worth_reviewing),
            "acked_total": len(acknowledged),
        },
    }


@app.route("/caregiver/alerts", methods=["GET"])
@role_required("caregiver", "doctor")
def caregiver_alerts():
    ctx = _caregiver_context()
    patient_id = ctx["active_patient_id"]
    if patient_id is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    alerts_data = generate_alerts_for_patient(patient_id)

    return render_template(
        "caregiver_alerts.html",
        ctx=ctx,
        alerts_data=alerts_data,
    )


@app.route("/caregiver/alerts/acknowledge", methods=["POST"])
@role_required("caregiver", "doctor")
def acknowledge_alert():
    """Mark an alert as acknowledged by the current user."""
    data = request.get_json() or {}
    alert_id = (data.get("alert_id") or "").strip()
    note = (data.get("note") or "").strip() or None

    if not alert_id:
        return jsonify({"error": "Missing alert_id"}), 400

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
        INSERT INTO alert_acknowledgements
            (alert_id, patient_id, acknowledged_by, note)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (alert_id, acknowledged_by) DO NOTHING
        """,
        (alert_id, patient_id, session["user_id"], note),
        commit=True,
    )

    return jsonify({"status": "acknowledged"})

@app.route("/doctor", methods=["GET"])
@role_required("doctor")
def doctor_dashboard():
    ctx = _doctor_context()
    if ctx["active_patient_id"] is None:
        return render_template("caregiver_no_patients.html", ctx=ctx)

    patient_summary = get_patient_summary(ctx["active_patient_id"])
    doctor_stats = get_doctor_stats_30d(ctx["active_patient_id"])

    return render_template(
        "doctor_dashboard.html",
        ctx=ctx,
        patient_summary=patient_summary,
        doctor_stats=doctor_stats,
    )

def _doctor_context():
    user_id = session["user_id"]
    assigned = list_assigned_patients(user_id, "doctor")
    active_patient_id = get_active_patient_id()
    active_patient_name = get_patient_display_name(active_patient_id) if active_patient_id else None
    return {
        "assigned_patients": assigned,
        "active_patient_id": active_patient_id,
        "active_patient_name": active_patient_name,
        "doctor_name": session.get("full_name", "Doctor"),
    }


@app.route("/doctor/select-patient/<int:patient_id>", methods=["POST", "GET"])
@role_required("doctor")
def doctor_select_patient(patient_id):
    if not assert_doctor_can_view(session["user_id"], patient_id):
        abort(403)

    session["viewing_patient_id"] = patient_id
    referrer = request.referrer
    if referrer and url_for("doctor_dashboard") in referrer:
        return redirect(referrer)
    return redirect(url_for("doctor_dashboard"))

def _calculate_age(dob):
    """Return integer age from a date object (or None)."""
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def get_patient_summary(patient_id):
    """Doctor header summary with safe fallbacks for missing columns/data."""
    if patient_id is None:
        return {
            "full_name": "No patient selected",
            "age": None,
            "patient_code": "PT-0000",
            "condition_tags": [],
        }

    
    row = run_query(
        """
        SELECT p.id, u.full_name
        FROM patients p
        JOIN users u ON u.id = p.user_id
        WHERE p.id = %s
        """,
        (patient_id,),
        fetchone=True,
    )

    if not row:
        return {
            "full_name": "Unknown patient",
            "age": None,
            "patient_code": f"PT-{patient_id:04d}",
            "condition_tags": [],
        }

    _, full_name = row

    
    age = None
    condition_tags = ["Hypertension", "Type 2 Diabetes"]  

    return {
        "full_name": full_name,
        "age": age,
        "patient_code": f"PT-{patient_id:04d}",
        "condition_tags": condition_tags,
    }

def get_doctor_stats_30d(patient_id):
    """Return doctor stat cards for the last 30 days."""
    if patient_id is None:
        return {
            "adherence_30d_pct": 0,
            "active_medications_count": 0,
            "side_effects_30d_count": 0,
            "last_checkin_label": "No check-ins",
        }

   
    meds_row = run_query(
        """
        SELECT COUNT(*)
        FROM medication_schedules
        WHERE patient_id = %s
        """,
        (patient_id,),
        fetchone=True,
    )
    active_medications_count = int(meds_row[0] or 0)

   
    taken_row = run_query(
        """
        SELECT COUNT(*)
        FROM medication_events
        WHERE patient_id = %s
          AND event_type = 'taken'
          AND created_at >= NOW() - INTERVAL '30 days'
        """,
        (patient_id,),
        fetchone=True,
    )
    taken_count_30d = int(taken_row[0] or 0)

    
    expected_30d = active_medications_count * 30
    adherence_30d_pct = round((taken_count_30d / expected_30d) * 100) if expected_30d else 0
    adherence_30d_pct = max(0, min(100, adherence_30d_pct))

   
    side_fx_row = run_query(
        """
        SELECT COUNT(*)
        FROM wellbeing_checkins
        WHERE patient_id = %s
          AND created_at >= NOW() - INTERVAL '30 days'
          AND side_effects IS NOT NULL
          AND TRIM(side_effects) <> ''
        """,
        (patient_id,),
        fetchone=True,
    )
    side_effects_30d_count = int(side_fx_row[0] or 0)

    last_checkin_row = run_query(
        """
        SELECT MAX(created_at)
        FROM wellbeing_checkins
        WHERE patient_id = %s
        """,
        (patient_id,),
        fetchone=True,
    )
    last_checkin_at = last_checkin_row[0] if last_checkin_row else None
    last_checkin_label = last_checkin_at.strftime("%d %b %Y, %H:%M") if last_checkin_at else "No check-ins"

    return {
        "adherence_30d_pct": adherence_30d_pct,
        "active_medications_count": active_medications_count,
        "side_effects_30d_count": side_effects_30d_count,
        "last_checkin_label": last_checkin_label,
    }

def _doctor_side_effect_severity(side_effect_text):
    """Map side effect text to mild/moderate for chart coloring."""
    text = (side_effect_text or "").strip().lower()
    if not text:
        return "mild"

    moderate_keywords = {
        "dizziness", "faint", "blurred", "palpitations",
        "chest pain", "shortness of breath", "vomiting", "severe",
    }
    if any(k in text for k in moderate_keywords):
        return "moderate"
    return "mild"


def _guess_medication_for_side_effect(side_effect_text, schedule):
    """Best-effort mapping from side-effect text to a medication name."""
    text = (side_effect_text or "").lower()
    for med in schedule:
        name = (med.get("name") or "").lower()
        if name and name in text:
            return med["name"]
    return "Overall regimen"


def build_doctor_adherence_side_effects_30d(patient_id):
    """Return labels, daily adherence %, and side-effect event dots for E4 chart."""
    schedule = get_schedule_data(patient_id)
    doses_per_day = len(schedule)
    today = datetime.now().date()
    start_day = today - timedelta(days=29)

    
    day_list = [start_day + timedelta(days=i) for i in range(30)]
    labels = [d.strftime("%d %b") for d in day_list]
    day_key = {d: d.strftime("%d %b") for d in day_list}

    
    taken_rows = run_query(
        """
        SELECT container_id, event_time, created_at::date AS day
        FROM medication_events
        WHERE patient_id = %s
          AND event_type = 'taken'
          AND created_at >= %s
        """,
        (patient_id, start_day),
    )

    
    taken_slots = set()
    for row in taken_rows:
        container_id = row[0] or ""
        event_time = parse_time_value(row[1])
        day = row[2]
        scheduled = None
        if ":" in container_id:
            _, _, scheduled_part = container_id.partition(":")
            scheduled = parse_time_value(scheduled_part)
        if scheduled is None:
            scheduled = event_time
        if day and scheduled:
            taken_slots.add((day, scheduled))

    
    adherence = []
    adherence_by_day = {}
    for d in day_list:
        if doses_per_day == 0:
            pct = 0
        else:
            taken_today = sum(1 for med in schedule if (d, med["time_obj"]) in taken_slots)
            pct = round((taken_today / doses_per_day) * 100)
        adherence.append(pct)
        adherence_by_day[d] = pct

    
    checkin_rows = run_query(
        """
        SELECT side_effects, created_at::date
        FROM wellbeing_checkins
        WHERE patient_id = %s
          AND created_at >= %s
          AND side_effects IS NOT NULL
          AND TRIM(side_effects) <> ''
        ORDER BY created_at ASC
        """,
        (patient_id, start_day),
    )

    events = []
    for side_effects, day in checkin_rows:
        if day not in adherence_by_day:
            continue
        severity = _doctor_side_effect_severity(side_effects)
        medication = _guess_medication_for_side_effect(side_effects, schedule)
        events.append({
            "date": day_key[day],
            "adherence": adherence_by_day[day],
            "severity": severity,
            "symptom": side_effects,
            "medication": medication,
        })

    return {
        "labels": labels,
        "adherence": adherence,
        "events": events,
    }

@app.route("/doctor/adherence-sideeffects-data", methods=["GET"])
@role_required("doctor")
def doctor_adherence_sideeffects_data():
    patient_id = get_active_patient_id()
    if patient_id is None:
        return jsonify({"labels": [], "adherence": [], "events": []})

    if not assert_doctor_can_view(session["user_id"], patient_id):
        abort(403)

    payload = build_doctor_adherence_side_effects_30d(patient_id)
    return jsonify(payload)

@app.route("/patient/care-team", methods=["GET"])
@role_required("patient")
def patient_care_team():
    return render_template("patient_care_team.html")


@app.route("/patient/settings", methods=["GET"])
@role_required("patient")
def patient_settings():
    return render_template("patient_settings.html")




if __name__ == "__main__":
    app.run(debug=True)