import streamlit as st
import pickle
import pandas as pd
import sqlite3
from datetime import date

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.set_page_config(
    page_title="Smart Hospital Management System",
    page_icon="🏥",
    layout="wide"
)


# =========================================================
# LOGIN SYSTEM
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🏥 Smart Hospital Management System")
    st.subheader("🔐 Login")

    username = st.text_input("👤 Username", key="login_username")
    password = st.text_input("🔑 Password", type="password", key="login_password")

    if st.button("🔐 Login", use_container_width=True, key="login_button"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Demo Login — Username: admin | Password: admin123")
    st.stop()

# -----------------------------
# Load ML Model
# -----------------------------
with open("disease_model.pkl", "rb") as f:
    model = pickle.load(f)

# -----------------------------
# Load Vectorizer
# -----------------------------
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# -----------------------------
# Database Connection
# -----------------------------
conn = sqlite3.connect(
    "hospital.db",
    check_same_thread=False
)

# -----------------------------
# Create Feedback Table if needed
# -----------------------------
conn.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    rating INTEGER,
    comments TEXT,
    feedback_date TEXT
)
""")
conn.commit()

# -----------------------------
# Load Disease Description
# -----------------------------
disease_description = pd.read_csv(
    "Disease_Description.csv",
    encoding="latin1"
)
disease_description.columns = [
    col.strip() for col in disease_description.columns
]

# -----------------------------
# Load Disease → Specialist
# -----------------------------
doctor_disease = pd.read_csv(
    "Doctor_Versus_Disease.csv",
    header=None,
    names=["Disease", "Specialist"],
    encoding="latin1"
)

doctor_disease["Disease"] = (
    doctor_disease["Disease"].astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

doctor_disease["Specialist"] = (
    doctor_disease["Specialist"].astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

# -----------------------------
# Page
# -----------------------------
st.title("🏥 Smart Hospital Management & Recommendation System")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🏥 Hospital System")

if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_button"):
    st.session_state.logged_in = False
    st.rerun()

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Disease Prediction",
        "Appointments",
        "Doctors",
        "Patients",
        "Patient History",
        "Analytics",
        "Reports & Feedback"
    ]
)

# =========================================================
# Dashboard
# =========================================================
if menu == "Dashboard":

    st.title("📊 Dashboard")

    total_patients = pd.read_sql_query("SELECT COUNT(*) AS count FROM patients", conn).iloc[0]["count"]
    total_doctors = pd.read_sql_query("SELECT COUNT(*) AS count FROM doctors", conn).iloc[0]["count"]
    total_appointments = pd.read_sql_query("SELECT COUNT(*) AS count FROM appointments", conn).iloc[0]["count"]
    pending_appointments = pd.read_sql_query("SELECT COUNT(*) AS count FROM appointments WHERE LOWER(status) IN ('booked','pending')", conn).iloc[0]["count"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Total Patients", total_patients)
    c2.metric("👨‍⚕️ Total Doctors", total_doctors)
    c3.metric("📅 Total Appointments", total_appointments)
    c4.metric("⏳ Pending", pending_appointments)

    st.divider()
    st.subheader("🏥 Smart Hospital Management System")
    st.write("Welcome to the Smart Hospital Management & Recommendation System.")

    st.subheader("✨ This System Provides")
    st.markdown("🔬 **Disease Prediction** — Predict possible disease from selected symptoms.")
    st.markdown("🩺 **Specialist Recommendation** — Recommend a suitable medical specialist.")
    st.markdown("👨‍⚕️ **Doctor Information** — View doctors and their duty schedules.")
    st.markdown("👤 **Patient Management** — Add and manage patient information.")
    st.markdown("📅 **Appointment Booking** — Book and manage patient appointments.")
    st.markdown("📜 **Patient History** — View previous patient visit records.")
    st.markdown("📈 **Analytics** — View hospital statistics and appointment trends.")
    st.markdown("🧾 **Medical Reports** — Generate downloadable patient reports.")
    st.markdown("⭐ **Patient Feedback** — Collect and view patient feedback.")

    st.subheader("📌 Quick Statistics")
    try:
        status_df = pd.read_sql_query("SELECT status, COUNT(*) AS count FROM appointments GROUP BY status", conn)
        if not status_df.empty:
            st.bar_chart(status_df.set_index("status")["count"])
    except Exception:
        pass

# =========================================================
# Appointments
# =========================================================
elif menu == "Appointments":

    st.header("📅 Appointment Management")

    patients = pd.read_sql_query(
        """
        SELECT patient_id, patient_name
        FROM patients
        ORDER BY patient_name
        """,
        conn
    )

    doctors = pd.read_sql_query(
        """
        SELECT doctor_id, doctor_name, specialization
        FROM doctors
        ORDER BY doctor_name
        """,
        conn
    )

    # -----------------------------
    # Appointment Date / Time
    # -----------------------------
    appointment_date = st.date_input(
        "📅 Appointment Date",
        value=date.today(),
        key="appointment_date"
    )

    appointment_time = st.time_input(
        "⏰ Appointment Time",
        key="appointment_time"
    )

    # -----------------------------
    # Patient Selection
    # -----------------------------
    patient_mode = st.radio(
        "👤 Patient",
        ["Existing Patient", "➕ Add New Patient"],
        horizontal=True,
        key="appointment_patient_mode"
    )

    selected_patient_id = None

    if patient_mode == "Existing Patient":

        patient_options = {
            f"{row['patient_name']} (ID: {row['patient_id']})":
            row["patient_id"]
            for _, row in patients.iterrows()
        }

        if patient_options:

            selected_patient = st.selectbox(
                "👤 Select Patient",
                list(patient_options.keys()),
                key="appointment_patient"
            )

            selected_patient_id = patient_options[selected_patient]

        else:
            st.warning("No patients found. Please add a new patient.")

    else:

        st.subheader("➕ New Patient Details")

        new_patient_name = st.text_input(
            "Patient Name",
            key="new_patient_name"
        )

        col1, col2 = st.columns(2)

        with col1:
            new_patient_age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=0,
                key="new_patient_age"
            )

        with col2:
            new_patient_gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other"],
                key="new_patient_gender"
            )

        new_patient_phone = st.text_input(
            "Phone Number",
            key="new_patient_phone"
        )

        new_patient_address = st.text_area(
            "Address",
            key="new_patient_address"
        )

        new_patient_symptoms = st.text_area(
            "Symptoms",
            key="new_patient_symptoms"
        )

        # New patient is saved together with appointment
        # so no separate Save Patient button is required.

    # -----------------------------
    # Select Doctor
    # -----------------------------
    doctor_options = {
        f"{row['doctor_name']} - {row['specialization']}":
        row["doctor_id"]
        for _, row in doctors.iterrows()
    }

    if doctor_options:

        selected_doctor = st.selectbox(
            "👨‍⚕️ Select Doctor",
            list(doctor_options.keys()),
            key="appointment_doctor"
        )

        selected_doctor_id = doctor_options[selected_doctor]

    else:

        st.warning("No doctors found.")
        selected_doctor_id = None

    # -----------------------------
    # Appointment Reason
    # -----------------------------
    reason = st.text_input(
        "📝 Reason for Appointment",
        key="appointment_reason"
    )

    # -----------------------------
    # Book Appointment
    # -----------------------------
    if st.button(
        "📅 Book Appointment",
        use_container_width=True,
        key="book_appointment"
    ):

        cursor = conn.cursor()

        try:

            # Add new patient first
            if patient_mode == "Add New Patient":

                if new_patient_name.strip() == "":
                    st.warning("Please enter patient name.")
                    st.stop()

                cursor.execute(
                    """
                    INSERT INTO patients
                    (
                        patient_name,
                        age,
                        gender,
                        phone,
                        address,
                        symptoms,
                        registration_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_patient_name.strip(),
                        new_patient_age,
                        new_patient_gender,
                        new_patient_phone,
                        new_patient_address,
                        new_patient_symptoms,
                        appointment_date.strftime("%Y-%m-%d")
                    )
                )

                selected_patient_id = cursor.lastrowid

            if selected_patient_id is None:
                st.warning("Please select or add a patient.")
                st.stop()

            if selected_doctor_id is None:
                st.warning("Please select a doctor.")
                st.stop()

            # Book appointment
            cursor.execute(
                """
                INSERT INTO appointments
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    status,
                    reason
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    selected_patient_id,
                    selected_doctor_id,
                    appointment_date.strftime("%Y-%m-%d"),
                    appointment_time.strftime("%H:%M"),
                    "Booked",
                    reason
                )
            )

            conn.commit()

            st.success(
                f"Appointment booked successfully! "
                f"Appointment ID: {cursor.lastrowid}"
            )

        except Exception as e:

            conn.rollback()
            st.error(f"Unable to book appointment: {e}")

    # -----------------------------
    # Appointment List
    # -----------------------------
    st.subheader("📋 Booked Appointments")

    appointments = pd.read_sql_query(
        """
        SELECT
            a.appointment_id,
            p.patient_name,
            d.doctor_name,
            d.specialization,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.reason
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.patient_id
        JOIN doctors d
            ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_id DESC
        """,
        conn
    )

    if appointments.empty:
        st.info("No appointments booked yet.")
    else:
        st.dataframe(
            appointments,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🔄 Update Appointment Status")
        appointment_ids = appointments["appointment_id"].tolist()
        if appointment_ids:
            aid = st.selectbox("Select Appointment ID", appointment_ids, key="status_appointment_id")
            new_status = st.selectbox("New Status", ["Booked", "Confirmed", "Completed", "Cancelled", "Pending"], key="new_appointment_status")
            if st.button("💾 Update Status", use_container_width=True, key="update_status"):
                conn.execute("UPDATE appointments SET status=? WHERE appointment_id=?", (new_status, int(aid)))
                conn.commit()
                st.success("Appointment status updated successfully!")
                st.rerun()

# =========================================================
# Doctors
# =========================================================
elif menu == "Doctors":

    st.header("👨‍⚕️ Doctors")

    doctors = pd.read_sql_query(
        """
        SELECT
            doctor_name,
            specialization,
            phone,
            email,
            room_number
        FROM doctors
        """,
        conn
    )

    st.dataframe(
        doctors,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------
    # Doctor Duty Schedule
    # -----------------------------
    st.subheader("🕒 Doctor Duty Schedule")

    shifts = pd.read_sql_query(
        """
        SELECT
            d.doctor_name,
            d.specialization,
            ds.duty_date,
            ds.shift_name,
            ds.start_time,
            ds.end_time,
            d.room_number,
            ds.status
        FROM doctor_shifts ds
        JOIN doctors d
            ON ds.doctor_id = d.doctor_id
        ORDER BY ds.duty_date DESC
        """,
        conn
    )

    st.dataframe(
        shifts,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# Patients
# =========================================================
elif menu == "Patients":

    st.header("👤 Patient Management")

    search = st.text_input("🔎 Search Patient by Name or Phone", key="patient_search")
    query = """SELECT patient_id, patient_name, age, gender, phone, address, symptoms, registration_date FROM patients"""
    params = ()
    if search.strip():
        query += " WHERE patient_name LIKE ? OR phone LIKE ?"
        params = (f"%{search.strip()}%", f"%{search.strip()}%")
    query += " ORDER BY patient_id DESC"
    patients = pd.read_sql_query(query, conn, params=params)

    if patients.empty:
        st.info("No patients found.")
    else:
        st.dataframe(patients, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("➕ Register New Patient")
    with st.form("patient_form"):
        name = st.text_input("Patient Name")
        a, b = st.columns(2)
        with a:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with b:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        phone = st.text_input("Phone Number")
        address = st.text_area("Address")
        symptoms = st.text_area("Symptoms")
        save_patient = st.form_submit_button("💾 Save Patient", use_container_width=True)

    if save_patient:
        if not name.strip():
            st.warning("Please enter patient name.")
        else:
            cur = conn.cursor()
            cur.execute("""INSERT INTO patients (patient_name, age, gender, phone, address, symptoms, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (name.strip(), age, gender, phone, address, symptoms, date.today().strftime("%Y-%m-%d")))
            conn.commit()
            st.success(f"Patient added successfully! Patient ID: {cur.lastrowid}")
            st.rerun()

# =========================================================
# Patient History
# =========================================================
elif menu == "Patient History":

    st.header("📜 Patient History")

    history = pd.read_sql_query(
        """
        SELECT
            ph.history_id AS "History ID",
            p.patient_name AS "Patient Name",
            d.doctor_name AS "Doctor Name",
            ph.visit_date AS "Visit Date",
            ph.department AS "Department",
            ph.symptoms AS "Symptoms",
            ph.notes AS "Notes"
        FROM patient_history ph
        LEFT JOIN patients p
            ON ph.patient_id = p.patient_id
        LEFT JOIN doctors d
            ON ph.doctor_id = d.doctor_id
        ORDER BY ph.visit_date DESC
        """,
        conn
    )

    if history.empty:
        st.info("No patient history found.")
    else:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

# =========================================================
# Analytics
# =========================================================
elif menu == "Analytics":

    st.header("📈 Hospital Analytics")

    st.subheader("📊 Appointment Status")
    status_df = pd.read_sql_query("SELECT status, COUNT(*) AS count FROM appointments GROUP BY status", conn)
    if status_df.empty:
        st.info("No appointment data available.")
    else:
        st.bar_chart(status_df.set_index("status")["count"])
        st.dataframe(status_df, use_container_width=True, hide_index=True)

    st.subheader("🏥 Department / Specialist-wise Doctors")
    spec_df = pd.read_sql_query("SELECT specialization, COUNT(*) AS doctors FROM doctors GROUP BY specialization ORDER BY doctors DESC", conn)
    if not spec_df.empty:
        st.bar_chart(spec_df.set_index("specialization")["doctors"])

    st.subheader("📅 Appointment Trend")
    trend_df = pd.read_sql_query("SELECT appointment_date, COUNT(*) AS appointments FROM appointments GROUP BY appointment_date ORDER BY appointment_date", conn)
    if not trend_df.empty:
        trend_df["appointment_date"] = pd.to_datetime(trend_df["appointment_date"], errors="coerce")
        trend_df = trend_df.dropna(subset=["appointment_date"]).set_index("appointment_date")
        st.line_chart(trend_df["appointments"])

# =========================================================
# Reports & Feedback
# =========================================================
elif menu == "Reports & Feedback":

    st.header("🧾 Medical Reports & Patient Feedback")

    patients = pd.read_sql_query("SELECT patient_id, patient_name FROM patients ORDER BY patient_name", conn)
    if patients.empty:
        st.info("No patients available.")
    else:
        pmap = {f"{r.patient_name} (ID: {r.patient_id})": int(r.patient_id) for _, r in patients.iterrows()}
        selected = st.selectbox("👤 Select Patient", list(pmap.keys()), key="report_patient")
        pid = pmap[selected]

        patient = pd.read_sql_query("SELECT * FROM patients WHERE patient_id=?", conn, params=(pid,))
        history = pd.read_sql_query("""SELECT ph.visit_date, d.doctor_name, ph.department, ph.symptoms, ph.notes FROM patient_history ph LEFT JOIN doctors d ON ph.doctor_id=d.doctor_id WHERE ph.patient_id=? ORDER BY ph.visit_date DESC""", conn, params=(pid,))
        appts = pd.read_sql_query("""SELECT a.appointment_date, a.appointment_time, d.doctor_name, d.specialization, a.status, a.reason FROM appointments a LEFT JOIN doctors d ON a.doctor_id=d.doctor_id WHERE a.patient_id=? ORDER BY a.appointment_date DESC""", conn, params=(pid,))

        st.subheader("📋 Patient Summary")
        st.dataframe(patient, use_container_width=True, hide_index=True)
      st.subheader("📅 Appointments")

if not appts.empty:
    st.dataframe(
        appts,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No appointments found.")

st.subheader("📜 Medical History")

if not history.empty:
    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No medical history found.")

        if REPORTLAB_AVAILABLE:
            from io import BytesIO
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, "Smart Hospital Management System")
            y -= 30
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, y, "Patient Medical Report")
            y -= 30
            c.setFont("Helvetica", 10)
            for col, val in patient.iloc[0].items():
                text = f"{col.replace('_',' ').title()}: {val}"
                c.drawString(50, y, text[:110])
                y -= 16
                if y < 60:
                    c.showPage(); y = height - 50; c.setFont("Helvetica", 10)
            y -= 10
            c.setFont("Helvetica-Bold", 11); c.drawString(50, y, "Appointments")
            y -= 18; c.setFont("Helvetica", 9)
            for _, r in appts.iterrows():
                text = f"{r['appointment_date']} {r['appointment_time']} | {r['doctor_name']} | {r['specialization']} | {r['status']}"
                c.drawString(50, y, text[:115]); y -= 14
                if y < 60:
                    c.showPage(); y = height - 50; c.setFont("Helvetica", 9)
            c.save(); buffer.seek(0)
            st.download_button("📥 Download Patient PDF Report", buffer.getvalue(), file_name=f"patient_report_{pid}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.warning("PDF library is not installed. Add reportlab to requirements.txt for PDF reports.")

    st.divider()
    st.subheader("⭐ Patient Feedback")
    feedback_patients = pd.read_sql_query("SELECT patient_id, patient_name FROM patients ORDER BY patient_name", conn)
    if not feedback_patients.empty:
        fmap = {f"{r.patient_name} (ID: {r.patient_id})": int(r.patient_id) for _, r in feedback_patients.iterrows()}
        fp = st.selectbox("Patient", list(fmap.keys()), key="feedback_patient")
        rating = st.slider("Rating", 1, 5, 5, key="feedback_rating")
        comments = st.text_area("Comments", key="feedback_comments")
        if st.button("⭐ Submit Feedback", use_container_width=True, key="submit_feedback"):
            conn.execute("INSERT INTO feedback (patient_id, rating, comments, feedback_date) VALUES (?, ?, ?, ?)", (fmap[fp], rating, comments, date.today().strftime("%Y-%m-%d")))
            conn.commit(); st.success("Thank you! Feedback submitted successfully.")

    feedback = pd.read_sql_query("SELECT f.feedback_id, p.patient_name, f.rating, f.comments, f.feedback_date FROM feedback f LEFT JOIN patients p ON f.patient_id=p.patient_id ORDER BY f.feedback_id DESC", conn)
    if not feedback.empty:
        st.subheader("📋 Feedback Records")
        st.dataframe(feedback, use_container_width=True, hide_index=True)

# =========================================================
# Disease Prediction
# =========================================================
elif menu == "Disease Prediction":

    st.title("🔬 Disease Prediction")

    st.write(
        "Select patient and symptoms for disease prediction."
    )

    # -----------------------------
    # Load Patients
    # -----------------------------
    patients_df = pd.read_sql_query(
        """
        SELECT patient_id, patient_name
        FROM patients
        ORDER BY patient_name
        """,
        conn
    )

    if patients_df.empty:

        st.warning(
            "No patients found. Please add a patient first."
        )

    else:

        patient_dict = dict(
            zip(
                patients_df["patient_name"],
                patients_df["patient_id"]
            )
        )

        selected_patient = st.selectbox(
            "👤 Select Patient",
            patients_df["patient_name"],
            key="disease_prediction_patient"
        )

        selected_patient_id = patient_dict[selected_patient]

        st.divider()

        # -----------------------------
        # Load Symptoms
        # -----------------------------
        symptom_df = pd.read_csv(
            "Symptom_Weights.csv",
            header=None,
            names=["Symptom", "Weight"],
            encoding="latin1"
        )

        symptom_df["Symptom"] = (
            symptom_df["Symptom"]
            .astype(str)
            .str.replace("_", " ", regex=False)
            .str.strip()
        )

        all_symptoms = sorted(
            symptom_df["Symptom"].unique()
        )

        # -----------------------------
        # Symptoms Selection
        # -----------------------------
        selected_symptoms = st.multiselect(
            "🩺 Select Symptoms",
            all_symptoms,
            key="disease_prediction_symptoms"
        )

        # -----------------------------
        # Predict Button
        # -----------------------------
        if st.button(
            "🔍 Predict Disease",
            use_container_width=True,
            key="predict_disease_button"
        ):

            if len(selected_symptoms) == 0:

                st.warning(
                    "Please select at least one symptom."
                )

            else:

                symptom_text = " ".join(selected_symptoms)

                symptom_vector = vectorizer.transform(
                    [symptom_text]
                )

                predicted_disease = model.predict(
                    symptom_vector
                )[0]

                # -----------------------------
                # Predicted Disease
                # -----------------------------
                st.success(
                    f"Predicted Disease: {predicted_disease}"
                )

                # -----------------------------
                # Disease Description
                # -----------------------------
                description_row = disease_description[
                    disease_description["Disease"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == predicted_disease.strip().lower()
                ]

                if not description_row.empty:

                    description = description_row.iloc[0]["Description"]

                    st.subheader("📋 Disease Description")
                    st.info(description)

                else:

                    description = "Description not available."
                    st.warning(description)

                # -----------------------------
                # Recommended Specialist
                # -----------------------------
                specialist_row = doctor_disease[
                    doctor_disease["Disease"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == predicted_disease.strip().lower()
                ]

                if not specialist_row.empty:

                    specialist = specialist_row.iloc[0]["Specialist"]

                    st.subheader("🩺 Recommended Specialist")
                    st.success(specialist)

                else:

                    specialist = "Specialist not available."
                    st.warning(specialist)

                # -----------------------------
                # Available Doctors
                # -----------------------------
                st.subheader("👨‍⚕️ Available Doctors")

                available_doctors = pd.read_sql_query(
                    """
                    SELECT
                        d.doctor_name AS Doctor,
                        d.specialization AS Specialist,
                        ds.shift_name AS Shift,
                        ds.start_time AS Start_Time,
                        ds.end_time AS End_Time,
                        d.room_number AS Room,
                        ds.status AS Status
                    FROM doctor_shifts ds
                    JOIN doctors d
                        ON ds.doctor_id = d.doctor_id
                    WHERE LOWER(TRIM(d.specialization))
                        = LOWER(TRIM(?))
                    AND ds.duty_date = ?
                    """,
                    conn,
                    params=(specialist, date.today().strftime("%Y-%m-%d"))
                )

                if not available_doctors.empty:

                    st.dataframe(
                        available_doctors,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        f"No available {specialist} doctors "
                        f"found for today."
                    )

                # -----------------------------
                # Save Information
                # -----------------------------
                st.session_state["patient_id"] = selected_patient_id
                st.session_state["predicted_disease"] = predicted_disease
                st.session_state["specialist"] = specialist
