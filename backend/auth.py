from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify
)
from werkzeug.security import check_password_hash


auth_bp = Blueprint("auth", __name__)



VALID_ROLES = ("patient", "caregiver", "doctor")


def _row_to_user(row):
    """Translate a (id, email, password_hash, full_name, role) tuple into a dict."""
    if row is None:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "full_name": row[3],
        "role": row[4],
    }


def find_user_by_email(run_query, email):
    """Look up a user by email. Returns a dict or None."""
    row = run_query(
        """
        SELECT id, email, password_hash, full_name, role
        FROM users
        WHERE email = %s
        """,
        (email,),
        fetchone=True,
    )
    return _row_to_user(row)


def find_patient_id_for_user(run_query, user_id):
    """Return patients.id for a patient user, or None."""
    row = run_query(
        """
        SELECT id
        FROM patients
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )
    return row[0] if row else None



def login_required(view):
    """Block the view unless someone is logged in. Otherwise -> /login."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Require a logged-in user with one of the given roles.

    Usage:
        @role_required("doctor")
        def doctor_dashboard(): ...
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
               
                return redirect(_default_landing_for_role(session.get("role")))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def _default_landing_for_role(role):
    """Where each role lands after login.

    Doctors don't have their dashboard yet (lands in AUTH-2). Until then
    they get a friendly placeholder that explains what's coming.
    """
    if role == "patient":
        return url_for("patient_dashboard")
    if role == "caregiver":
        return url_for("caregiver_dashboard")
    if role == "doctor":
        return url_for("auth.doctor_placeholder")
    return url_for("auth.login")



@auth_bp.route("/login", methods=["GET"])
def login():
    """Render the tabbed login page. Default tab: patient."""
    return render_template("login.html", active_tab="patient", error=None)


@auth_bp.route("/login/<role>", methods=["GET"])
def login_with_tab(role):
    """Direct link to a specific tab, e.g. /login/caregiver."""
    if role not in VALID_ROLES:
        return redirect(url_for("auth.login"))
    return render_template("login.html", active_tab=role, error=None)


@auth_bp.route("/login", methods=["POST"])
def login_submit():
    """Validate email + password and start a session.

    Form fields:
      role      — which tab the user was on
      email
      password
    """
   
    from app import run_query

    role = (request.form.get("role") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if role not in VALID_ROLES:
        return render_template(
            "login.html", active_tab="patient",
            error="Please pick a role tab and try again."
        ), 400

    user = find_user_by_email(run_query, email)

   
    invalid_error = "Email or password is incorrect."

    if user is None:
        return render_template(
            "login.html", active_tab=role, error=invalid_error
        ), 401

    if not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", active_tab=role, error=invalid_error
        ), 401

    if user["role"] != role:
      
        return render_template(
            "login.html", active_tab=role, error=invalid_error
        ), 401

   
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["full_name"] = user["full_name"]

    if user["role"] == "patient":
        session["patient_id"] = find_patient_id_for_user(run_query, user["id"])

    return redirect(_default_landing_for_role(user["role"]))


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    """Wipe the session and bounce to /login."""
    session.clear()
    return redirect(url_for("auth.login"))



@auth_bp.route("/doctor/dashboard")
def doctor_placeholder():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template(
        "doctor_placeholder.html",
        full_name=session.get("full_name", "Doctor"),
    )



@auth_bp.route("/auth/whoami", methods=["GET"])
def whoami():
    """Returns the current session contents as JSON. Diagnostic only."""
    if "user_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "user_id": session.get("user_id"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
        "patient_id": session.get("patient_id"),
    })
