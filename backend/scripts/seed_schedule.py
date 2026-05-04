import psycopg2


DB_CONFIG = {
    "dbname": "smart_medication_db",
    "user": "kowtharabdiqadir",
    "host": "localhost",
}
DEMO_PATIENT_EMAIL = "patient@meditrack.demo"
SCHEDULE = [
    ("Blood Pressure Medication", "08:00", "1 tablet"),
    ("Vitamin D",                 "12:00", "1 tablet"),
    ("Iron Tablet",               "18:00", "1 tablet"),
    ("Metformin",                 "20:00", "1 tablet"),
]
def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # Find the patient_id 
        cur.execute(
            """
            SELECT p.id
            FROM patients p
            JOIN users u ON u.id = p.user_id
            WHERE u.email = %s
            """,
            (DEMO_PATIENT_EMAIL,),
        )
        row = cur.fetchone()
        if row is None:
            print(f"ERROR: no patient record for {DEMO_PATIENT_EMAIL}.")
            print("Run the AUTH-1 seed_users.py first.")
            return
        patient_id = row[0]
        cur.execute(
            "DELETE FROM medication_schedules WHERE patient_id = %s",
            (patient_id,),
        )
        for name, scheduled_time, dose in SCHEDULE:
            cur.execute(
                """
                INSERT INTO medication_schedules
                    (patient_id, medication_name, scheduled_time, dose)
                VALUES (%s, %s, %s, %s)
                """,
                (patient_id, name, scheduled_time, dose),
            )
        conn.commit()
        print(f"Seeded {len(SCHEDULE)} schedule rows for patient_id={patient_id}.")
        for name, scheduled_time, dose in SCHEDULE:
            print(f"  {scheduled_time}  {name:30s}  {dose}")
    finally:
        cur.close()
        conn.close()
if __name__ == "__main__":
    main()