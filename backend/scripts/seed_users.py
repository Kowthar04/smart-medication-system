import psycopg2
from werkzeug.security import generate_password_hash


DB_CONFIG = {
    "dbname": "smart_medication_db",
    "user": "kowtharabdiqadir",
    "host": "localhost",
}


DEMO_PASSWORD = "demo1234"

DEMO_USERS = [
    {
        "email": "patient@meditrack.demo",
        "full_name": "Sarah Khan",
        "role": "patient",
    },
    {
        "email": "caregiver@meditrack.demo",
        "full_name": "Nurse Jane",
        "role": "caregiver",
    },
    {
        "email": "doctor@meditrack.demo",
        "full_name": "Dr. Smith",
        "role": "doctor",
    },
]


def upsert_user(cur, email, password_hash, full_name, role):
    """Create the user if it doesn't exist, or refresh password+name if it does."""
    cur.execute(
        """
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE
          SET password_hash = EXCLUDED.password_hash,
              full_name     = EXCLUDED.full_name
        RETURNING id
        """,
        (email, password_hash, full_name, role),
    )
    return cur.fetchone()[0]


def ensure_patient_record(cur, user_id):
    """Create the matching patients row for a patient user."""
    cur.execute(
        """
        INSERT INTO patients (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        password_hash = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")

        print("Seeding demo accounts...")
        print()

        for u in DEMO_USERS:
            user_id = upsert_user(
                cur,
                email=u["email"],
                password_hash=password_hash,
                full_name=u["full_name"],
                role=u["role"],
            )

            if u["role"] == "patient":
                ensure_patient_record(cur, user_id)

            print(f"  [{u['role']:9s}] {u['email']:35s}  {u['full_name']}")

        conn.commit()

        print()
        print(f"Done. All accounts use password: {DEMO_PASSWORD}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()