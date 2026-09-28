import streamlit as st
import pickle
import pandas as pd
import sqlite3
from pathlib import Path
import io

# PDF जनरेशनसाठी ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------
# File Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent

def find_file(filename, folder=None):
    candidates = []
    if folder:
        candidates.append(BASE_DIR / folder / filename)
    candidates.append(BASE_DIR / filename)

    for path in candidates:
        if path.exists():
            return path

    searched = "\n".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"File not found: {filename}\nChecked:\n{searched}"
    )

st.set_page_config(
    page_title="Smart Hospital Management System",
    page_icon="🏥",
    layout="wide"
)

# -----------------------------
# PDF Generator Function (New Feature)
# -----------------------------
def generate_pdf_report(patient_name, symptoms, disease, description, specialist):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=15
    )
    story.append(Paragraph("🏥 Smart Hospital Diagnostic Report", title_style))
    story.append(Spacer(1, 10))

    # Patient & Diagnosis Details Table
    data = [
        [Paragraph("<b>Patient Name:</b>", styles['Normal']), Paragraph(patient_name, styles['Normal'])],
        [Paragraph("<b>Reported Symptoms:</b>", styles['Normal']), Paragraph(", ".join(symptoms), styles['Normal'])],
        [Paragraph("<b>Predicted Disease:</b>", styles['Normal']), Paragraph(f"<font color='red'><b>{disease}</b></font>", styles['Normal'])],
        [Paragraph("<b>Recommended Specialist:</b>", styles['Normal']), Paragraph(f"<b>{specialist}</b>", styles['Normal'])],
        [Paragraph("<b>Description:</b>", styles['Normal']), Paragraph(description, styles['Normal'])]
    ]

    t = Table(data, colWidths=[150, 380])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FBFF")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Footer note
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Italic'], fontSize=9, textColor=colors.gray)
    story.append(Paragraph("Note: This is an AI-generated preliminary report. Please consult a qualified medical professional for exact diagnosis.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


# -----------------------------
# Login Page
# -----------------------------
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown(
        """
        <style>
        .login-title { text-align: center; font-size: 34px; font-weight: 700; margin-top: 35px; margin-bottom: 5px; }
        .login-subtitle { text-align: center; font-size: 16px; margin-bottom: 25px; }
        .login-card { padding: 25px; border-radius: 15px; border: 1px solid #d9e2ec; background: #f8fbff; box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-title">🏥 Smart Hospital Management System</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Secure Hospital Management & Recommendation Portal</div>', unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.35, 1])
    with center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("🔐 Sign In")
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
        login_button = st.button("🚪 Login", use_container_width=True)

        if login_button:
            if username == DEMO_USERNAME and password == DEMO_PASSWORD:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("---")
        st.caption("Demo Login -> Username: admin | Password: admin123")
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# -----------------------------
# Load ML Model & Vectorizer
# -----------------------------
with open(find_file("disease_model.pkl", "model"), "rb") as f:
    model = pickle.load(f)

with open(find_file("vectorizer.pkl", "model"), "rb") as f:
    vectorizer = pickle.load(f)

# -----------------------------
# Database Connection
# -----------------------------
conn = sqlite3.connect(
    find_file("hospital.db", "database"),
    check_same_thread=False
)

# Load CSVS
disease_description = pd.read_csv(find_file("Disease_Description.csv", "data"), encoding="latin1")
disease_description.columns = [col.strip() for col in disease_description.columns]

doctor_disease = pd.read_csv(find_file("Doctor_Versus_Disease.csv", "data"), header=None, names=["Disease", "Specialist"], encoding="latin1")
doctor_disease["Disease"] = doctor_disease["Disease"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()
doctor_disease["Specialist"] = doctor_disease["Specialist"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()

# -----------------------------
# Sidebar & Navigation
# -----------------------------
st.sidebar.title("🏥 Hospital System")
st.sidebar.success("🟢 Logged in as: Admin")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.divider()

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Disease Prediction", "Appointments", "Doctors", "Patients", "Patient History"]
)

# -----------------------------
# Dashboard
# -----------------------------
if menu == "Dashboard":
    st.title("📊 Dashboard")
    total_patients = pd.read_sql_query("SELECT COUNT(*) AS count FROM patients", conn).iloc[0]["count"]
    total_doctors = pd.read_sql_query("SELECT COUNT(*) AS count FROM doctors", conn).iloc[0]["count"]
    total_appointments = pd.read_sql_query("SELECT COUNT(*) AS count FROM appointments", conn).iloc[0]["count"]

    col1, col2, col3 = st.columns(3)
    col1.metric("👤 Total Patients", total_patients)
    col2.metric("👨‍⚕️ Total Doctors", total_doctors)
    col3.metric("📅 Total Appointments", total_appointments)

    st.divider()
    st.subheader("🏥 Smart Hospital Management System")
    st.write("""
    Welcome to the Smart Hospital Management System.
    - 🔬 Disease prediction from symptoms
    - 🩺 Specialist recommendation
    - 👨‍⚕️ Available doctor information
    - 👤 Patient management & New Registration
    - 📅 Appointment booking
    - 📜 Patient history & PDF Medical Reports
    """)

# -----------------------------
# Appointments
# -----------------------------
elif menu == "Appointments":
    st.header("📅 Appointment Management")
    patients = pd.read_sql_query("SELECT patient_id, patient_name FROM patients", conn)
    doctors = pd.read_sql_query("SELECT doctor_id, doctor_name, specialization FROM doctors", conn)

    if not patients.empty and not doctors.empty:
        patient_options = {f"{row['patient_name']} (ID: {row['patient_id']})": row["patient_id"] for _, row in patients.iterrows()}
        selected_patient = st.selectbox("👤 Select Patient", list(patient_options.keys()), key="appointment_patient")
        selected_patient_id = patient_options[selected_patient]

        doctor_options = {f"{row['doctor_name']} - {row['specialization']}": row["doctor_id"] for _, row in doctors.iterrows()}
        selected_doctor = st.selectbox("👨‍⚕️ Select Doctor", list(doctor_options.keys()), key="appointment_doctor")
        selected_doctor_id = doctor_options[selected_doctor]

        appointment_date = st.date_input("📅 Appointment Date", key="appointment_date")
        appointment_time = st.time_input("⏰ Appointment Time", key="appointment_time")
        reason = st.text_input("📝 Reason for Appointment", key="appointment_reason")

        if st.button("📅 Book Appointment", use_container_width=True, key="book_appointment"):
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, reason)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (selected_patient_id, selected_doctor_id, appointment_date.strftime("%Y-%m-%d"), appointment_time.strftime("%H:%M"), "Booked", reason)
            )
            conn.commit()
            st.success(f"Appointment booked successfully! ID: {cursor.lastrowid}")
    else:
        st.warning("Please add patients and doctors first.")

    st.subheader("📋 Booked Appointments")
    appointments = pd.read_sql_query(
        """SELECT a.appointment_id, p.patient_name, d.doctor_name, d.specialization, a.appointment_date, a.appointment_time, a.status, a.reason
           FROM appointments a JOIN patients p ON a.patient_id = p.patient_id JOIN doctors d ON a.doctor_id = d.doctor_id ORDER BY a.appointment_id DESC""",
        conn
    )
    if appointments.empty:
        st.info("No appointments booked yet.")
    else:
        st.dataframe(appointments, use_container_width=True, hide_index=True)

# -----------------------------
# Doctors
# -----------------------------
elif menu == "Doctors":
    st.header("👨‍⚕️ Doctors")
    doctors = pd.read_sql_query("SELECT doctor_name, specialization, phone, email, room_number FROM doctors", conn)
    st.dataframe(doctors, use_container_width=True, hide_index=True)

    st.subheader("🕒 Doctor Duty Schedule")
    shifts = pd.read_sql_query(
        """SELECT d.doctor_name, d.specialization, ds.duty_date, ds.shift_name, ds.start_time, ds.end_time, d.room_number, ds.status
           FROM doctor_shifts ds JOIN doctors d ON ds.doctor_id = d.doctor_id ORDER BY ds.duty_date DESC""",
        conn
    )
    st.dataframe(shifts, use_container_width=True, hide_index=True)

# -----------------------------
# Patients (New Patient Add Feature)
# -----------------------------
elif menu == "Patients":
    st.header("👤 Patient Management")

    # Add New Patient Form
    with st.expander("➕ Add New Patient"):
        with st.form("add_patient_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_name = st.text_input("Patient Name*")
                p_age = st.number_input("Age*", min_value=1, max_value=120, value=25)
                p_gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            with col2:
                p_phone = st.text_input("Phone Number")
                p_address = st.text_area("Address")
                p_symptoms = st.text_input("Initial Symptoms")

            submit_patient = st.form_submit_button("Save Patient")

            if submit_patient:
                if not p_name:
                    st.error("Patient Name is required!")
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO patients (patient_name, age, gender, phone, address, symptoms, registration_date)
                           VALUES (?, ?, ?, ?, ?, ?, DATE('now'))""",
                        (p_name, p_age, p_gender, p_phone, p_address, p_symptoms)
                    )
                    conn.commit()
                    st.success(f"Patient '{p_name}' added successfully!")
                    st.rerun()

    st.subheader("📋 Registered Patients List")
    patients = pd.read_sql_query("SELECT patient_id, patient_name, age, gender, phone, address, symptoms, registration_date FROM patients ORDER BY patient_id DESC", conn)
    st.dataframe(patients, use_container_width=True, hide_index=True)

# -----------------------------
# Patient History
# -----------------------------
elif menu == "Patient History":
    st.header("📜 Patient History")
    history = pd.read_sql_query(
        """SELECT ph.history_id AS "History ID", p.patient_name AS "Patient Name", d.doctor_name AS "Doctor Name",
           ph.visit_date AS "Visit Date", ph.department AS "Department", ph.symptoms AS "Symptoms", ph.notes AS "Notes"
           FROM patient_history ph LEFT JOIN patients p ON ph.patient_id = p.patient_id LEFT JOIN doctors d ON ph.doctor_id = d.doctor_id ORDER BY ph.visit_date DESC""",
        conn
    )
    if history.empty:
        st.info("No patient history found.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

# -----------------------------
# Disease Prediction (+ PDF Feature)
# -----------------------------
elif menu == "Disease Prediction":
    st.title("🔬 Disease Prediction & Recommendation")

    patients_df = pd.read_sql_query("SELECT patient_id, patient_name FROM patients ORDER BY patient_name", conn)

    if patients_df.empty:
        st.warning("No patients registered yet. Please add a patient in the 'Patients' menu first.")
    else:
        patient_dict = dict(zip(patients_df["patient_name"], patients_df["patient_id"]))
        selected_patient = st.selectbox("👤 Select Patient", patients_df["patient_name"], key="disease_prediction_patient")
        selected_patient_id = patient_dict[selected_patient]

        st.divider()

        symptom_df = pd.read_csv(find_file("Symptom_Weights.csv", "data"), header=None, names=["Symptom", "Weight"], encoding="latin1")
        symptom_df["Symptom"] = symptom_df["Symptom"].astype(str).str.replace("_", " ", regex=False).str.strip()
        all_symptoms = sorted(symptom_df["Symptom"].unique())

        selected_symptoms = st.multiselect("🩺 Select Symptoms", all_symptoms, key="disease_prediction_symptoms")

        if st.button("🔍 Predict Disease", use_container_width=True, key="predict_disease_button"):
            if len(selected_symptoms) == 0:
                st.warning("Please select at least one symptom.")
            else:
                symptom_text = " ".join(selected_symptoms)
                symptom_vector = vectorizer.transform([symptom_text])
                predicted_disease = model.predict(symptom_vector)[0]

                st.success(f"Predicted Disease: **{predicted_disease}**")

                # Description
                description_row = disease_description[disease_description["Disease"].astype(str).str.strip().str.lower() == predicted_disease.strip().lower()]
                description = description_row.iloc[0]["Description"] if not description_row.empty else "Description not available."

                st.subheader("📋 Disease Description")
                st.info(description)

                # Specialist
                specialist_row = doctor_disease[doctor_disease["Disease"].astype(str).str.strip().str.lower() == predicted_disease.strip().lower()]
                specialist = specialist_row.iloc[0]["Specialist"] if not specialist_row.empty else "General Physician"

                st.subheader("🩺 Recommended Specialist")
                st.success(specialist)

                # Save session state
                st.session_state["last_prediction"] = {
                    "patient_name": selected_patient,
                    "symptoms": selected_symptoms,
                    "disease": predicted_disease,
                    "description": description,
                    "specialist": specialist
                }

                # Available Doctors
                st.subheader("👨‍⚕️ Available Doctors")
                duty_date = st.date_input("📅 Check Doctor Availability For", value=pd.to_datetime("2026-08-24").date(), key="doctor_availability_date")
                duty_date_str = duty_date.strftime("%Y-%m-%d")

                available_doctors = pd.read_sql_query(
                    """SELECT d.doctor_name AS Doctor, d.specialization AS Specialist, ds.shift_name AS Shift,
                              ds.start_time AS Start_Time, ds.end_time AS End_Time, d.room_number AS Room, ds.status AS Status
                       FROM doctor_shifts ds JOIN doctors d ON ds.doctor_id = d.doctor_id
                       WHERE LOWER(TRIM(d.specialization)) = LOWER(TRIM(?)) AND ds.duty_date = ? AND LOWER(TRIM(ds.status)) = 'available'""",
                    conn, params=(specialist, duty_date_str)
                )

                if not available_doctors.empty:
                    st.dataframe(available_doctors, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No available {specialist} doctors found for {duty_date_str}.")

        # Download PDF Section
        if "last_prediction" in st.session_state:
            st.divider()
            st.subheader("📄 Download Diagnostic Report")
            pred_data = st.session_state["last_prediction"]
            pdf_bytes = generate_pdf_report(
                pred_data["patient_name"],
                pred_data["symptoms"],
                pred_data["disease"],
                pred_data["description"],
                pred_data["specialist"]
            )
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Report_{pred_data['patient_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
