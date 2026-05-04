import psycopg2


DB_CONFIG = {
    "dbname": "smart_medication_db",
    "user": "kowtharabdiqadir",
    "host": "localhost",
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email = 'patient@meditrack.demo'")
        row = cur.fetchone()
        patient_user_id = row[0] if row else None

        cur.execute("SELECT id FROM users WHERE email = 'caregiver@meditrack.demo'")
        row = cur.fetchone()
        caregiver_user_id = row[0] if row else None

        cur.execute("SELECT id FROM users WHERE email = 'doctor@meditrack.demo'")
        row = cur.fetchone()
        doctor_user_id = row[0] if row else None

        if not patient_user_id:
            print("ERROR: patient@meditrack.demo doesn't exist. Run seed_users.py first.")
            return
        cur.execute(
            "SELECT id FROM patients WHERE user_id = %s",
            (patient_user_id,),
        )
        row = cur.fetchone()
        patient_clinical_id = row[0] if row else None
        if not patient_clinical_id:
            print("ERROR: patient row missing in `patients` table.")
            print("Run scripts/seed_users.py — it creates the patient record.")
            return
        if caregiver_user_id:
            cur.execute(
                """
                INSERT INTO caregiver_patient (caregiver_id, patient_id)
                VALUES (%s, %s)
                ON CONFLICT (caregiver_id, patient_id) DO NOTHING
                """,
                (caregiver_user_id, patient_clinical_id),
            )
            print(f"  caregiver -> patient assignment ensured")
        else:
            print("  no caregiver demo account (skipping)")
        if doctor_user_id:
            cur.execute(
                """
                INSERT INTO doctor_patient (doctor_id, patient_id)
                VALUES (%s, %s)
                ON CONFLICT (doctor_id, patient_id) DO NOTHING
                """,
                (doctor_user_id, patient_clinical_id),
            )
            print(f"  doctor -> patient assignment ensured")
        else:
            print("  no doctor demo account (skipping)")
        conn.commit()
        # Verify.
        cur.execute("SELECT COUNT(*) FROM caregiver_patient")
        cg_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM doctor_patient")
        dr_count = cur.fetchone()[0]
        print()
        print(f"caregiver_patient rows: {cg_count}")
        print(f"doctor_patient rows:    {dr_count}")
    finally:
        cur.close()
        conn.close()
if __name__ == "__main__":
    main()