import streamlit as st
import pickle
import pandas as pd
import sqlite3
from pathlib import Path
import io

# Visuals & Statistics sathi
import plotly.express as px

# PDF Generation sathi ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------
# File Paths & Setup
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
    raise FileNotFoundError(f"File not found: {filename}\nChecked:\n{searched}")

st.set_page_config(
    page_title="Smart Hospital Management System",
    page_icon="🏥",
    layout="wide"
)

# -----------------------------
# Database Setup & Initialization
# -----------------------------
conn = sqlite3.connect(find_file("hospital.db", "database"), check_same_thread=False)

def init_db():
    cursor = conn.cursor()
    # Feedback Table तयार नसलास
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            rating INTEGER,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

init_db()

# Load CSVs
disease_description = pd.read_csv(find_file("Disease_Description.csv", "data"), encoding="latin1")
disease_description.columns = [col.strip() for col in disease_description.columns]

doctor_disease = pd.read_csv(find_file("Doctor_Versus_Disease.csv", "data"), header=None, names=["Disease", "Specialist"], encoding="latin1")
doctor_disease["Disease"] = doctor_disease["Disease"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()
doctor_disease["Specialist"] = doctor_disease["Specialist"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()

# Load ML Model
with open(find_file("disease_model.pkl", "model"), "rb") as f:
    model = pickle.load(f)

with open(find_file("vectorizer.pkl", "model"), "rb") as f:
    vectorizer = pickle.load(f)

# -----------------------------
# PDF Generator Helper
# -----------------------------
def generate_pdf_report(patient_name, age, gender, phone, symptoms, disease, description, specialist, medicines="", doctor_notes=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle(
        'HeaderStyle', parent=styles['Heading1'], fontSize=20,
        textColor=colors.HexColor("#0D3B66"), alignment=1, spaceAfter=15
    )
    story.append(Paragraph("🏥 SMART HOSPITAL MEDICAL REPORT & PRESCRIPTION", header_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>👤 Patient Information</b>", styles['Heading2']))
    patient_data = [
        [Paragraph(f"<b>Name:</b> {patient_name}", styles['Normal']), Paragraph(f"<b>Age/Gender:</b> {age} / {gender}", styles['Normal'])],
        [Paragraph(f"<b>Phone:</b> {phone}", styles['Normal']), Paragraph(f"<b>Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}", styles['Normal'])]
    ]
    t_patient = Table(patient_data, colWidths=[270, 270])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BCCCDC")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_patient)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>🔬 Clinical Prediction & Diagnosis</b>", styles['Heading2']))
    diag_data = [
        [Paragraph("<b>Selected Symptoms:</b>", styles['Normal']), Paragraph(", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms), styles['Normal'])],
        [Paragraph("<b>Predicted Disease:</b>", styles['Normal']), Paragraph(f"<font color='#D90429'><b>{disease}</b></font>", styles['Normal'])],
        [Paragraph("<b>Recommended Specialist:</b>", styles['Normal']), Paragraph(f"<b>{specialist}</b>", styles['Normal'])],
        [Paragraph("<b>Disease Summary:</b>", styles['Normal']), Paragraph(description, styles['Normal'])]
    ]

    t_diag = Table(diag_data, colWidths=[150, 390])
    t_diag.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_diag)
    story.append(Spacer(1, 15))

    if medicines or doctor_notes:
        story.append(Paragraph("<b>💊 Prescribed Medicines & Doctor Advice</b>", styles['Heading2']))
        rx_data = [
            [Paragraph("<b>Rx / Medicines:</b>", styles['Normal']), Paragraph(medicines if medicines else "As advised by doctor.", styles['Normal'])],
            [Paragraph("<b>Doctor Notes:</b>", styles['Normal']), Paragraph(doctor_notes if doctor_notes else "Rest and follow up after 5 days.", styles['Normal'])]
        ]
        t_rx = Table(rx_data, colWidths=[150, 390])
        t_rx.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEA")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F6AD55")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_rx)
        story.append(Spacer(1, 15))

    footer_style = ParagraphStyle('FooterStyle', parent=styles['Italic'], fontSize=8, textColor=colors.gray, alignment=1)
    story.append(Paragraph("Note: This is an automated preliminary medical report generated by Smart Hospital AI. Please consult a registered doctor for clinical verification.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# -----------------------------
# Login Management
# -----------------------------
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🏥 Smart Hospital Management & Recommendation System")
    st.subheader("🔐 Sign In")
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    if st.button("🚪 Login", use_container_width=True):
        if username == DEMO_USERNAME and password == DEMO_PASSWORD:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# -----------------------------
# Sidebar Navigation
# -----------------------------
st.sidebar.title("🏥 Hospital System")

if st.sidebar.button("📙 Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Disease Prediction",
        "Appointments",
        "Doctors & Duty Schedule",
        "Patient Management",
        "Patient History & Search",
        "Analytics & Trends",
        "Reports & Feedback"
    ]
)

st.title("🏥 Smart Hospital Management & Recommendation System")

# -----------------------------
# 1. Dashboard
# -----------------------------
if menu == "Dashboard":
    st.header("📊 Advanced Dashboard")
    
    total_patients = pd.read_sql_query("SELECT COUNT(*) AS count FROM patients", conn).iloc[0]["count"]
    total_doctors = pd.read_sql_query("SELECT COUNT(*) AS count FROM doctors", conn).iloc[0]["count"]
    total_appointments = pd.read_sql_query("SELECT COUNT(*) AS count FROM appointments", conn).iloc[0]["count"]
    pending = pd.read_sql_query("SELECT COUNT(*) AS count FROM appointments WHERE LOWER(status)='pending' OR LOWER(status)='booked'", conn).iloc[0]["count"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Total Patients", total_patients)
    col2.metric("👨‍⚕️️ Total Doctors", total_doctors)
    col3.metric("📅 Total Appointments", total_appointments)
    col4.metric("⏳ Pending Appointments", pending)

    st.divider()

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📌 Appointment Status Overview")
        app_status_df = pd.read_sql_query("SELECT status, COUNT(*) as count FROM appointments GROUP BY status", conn)
        if not app_status_df.empty:
            fig_quick = px.pie(app_status_df, names='status', values='count', hole=0.4, title="Status Breakdown")
            st.plotly_chart(fig_quick, use_container_width=True)
        else:
            st.info("No appointment statistics available.")

    with col_chart2:
        st.subheader("⭐ Recent Patient Feedbacks")
        fb_df = pd.read_sql_query("SELECT patient_name, rating, comments FROM feedback ORDER BY feedback_id DESC LIMIT 3", conn)
        if not fb_df.empty:
            st.dataframe(fb_df, use_container_width=True, hide_index=True)
        else:
            st.info("No feedback recorded yet.")

# -----------------------------
# 2. Disease Prediction
# -----------------------------
elif menu == "Disease Prediction":
    st.header("🔬 AI Disease Prediction & Specialist Recommendation")
    
    patients_df = pd.read_sql_query("SELECT patient_id, patient_name, age, gender, phone FROM patients ORDER BY patient_name", conn)

    if patients_df.empty:
        st.warning("No patients registered. Please register patients first.")
    else:
        patient_map = {row['patient_name']: row for _, row in patients_df.iterrows()}
        selected_patient_name = st.selectbox("👤 Select Patient", list(patient_map.keys()))
        selected_patient_info = patient_map[selected_patient_name]

        symptom_df = pd.read_csv(find_file("Symptom_Weights.csv", "data"), header=None, names=["Symptom", "Weight"], encoding="latin1")
        symptom_df["Symptom"] = symptom_df["Symptom"].astype(str).str.replace("_", " ", regex=False).str.strip()
        all_symptoms = sorted(symptom_df["Symptom"].unique())

        selected_symptoms = st.multiselect("🩺 Select Symptoms", all_symptoms)

        with st.expander("💊 Prescribe Medicines & Add Doctor Notes (Optional)"):
            rx_medicines = st.text_area("Medicines", value="Paracetamol 500mg (1-0-1)")
            rx_notes = st.text_area("Doctor Advice", value="Take rest, drink warm water.")

        if st.button("🔍 Predict Disease"):
            if not selected_symptoms:
                st.warning("Please select at least one symptom.")
            else:
                symptom_text = " ".join(selected_symptoms)
                symptom_vector = vectorizer.transform([symptom_text])
                predicted_disease = model.predict(symptom_vector)[0]

                st.success(f"Predicted Disease: **{predicted_disease}**")

                description_row = disease_description[disease_description["Disease"].astype(str).str.strip().str.lower() == predicted_disease.strip().lower()]
                description = description_row.iloc[0]["Description"] if not description_row.empty else "Detailed description not available."

                st.subheader("📋 Disease Description")
                st.info(description)

                specialist_row = doctor_disease[doctor_disease["Disease"].astype(str).str.strip().str.lower() == predicted_disease.strip().lower()]
                specialist = specialist_row.iloc[0]["Specialist"] if not specialist_row.empty else "General Physician"

                st.subheader("🩺 Recommended Specialist")
                st.success(f"**{specialist}**")

                st.session_state["last_prediction"] = {
                    "patient_name": selected_patient_info["patient_name"],
                    "age": selected_patient_info.get("age", "N/A"),
                    "gender": selected_patient_info.get("gender", "N/A"),
                    "phone": selected_patient_info.get("phone", "N/A"),
                    "symptoms": selected_symptoms,
                    "disease": predicted_disease,
                    "description": description,
                    "specialist": specialist,
                    "medicines": rx_medicines,
                    "notes": rx_notes
                }

                # Recommended Doctor Schedule Display
                st.subheader("👨‍⚕️ Available Recommended Doctors")
                available_doctors = pd.read_sql_query(
                    """SELECT d.doctor_name AS Doctor, d.specialization AS Specialist, ds.shift_name AS Shift,
                              ds.start_time AS Start_Time, ds.end_time AS End_Time, d.room_number AS Room
                       FROM doctor_shifts ds JOIN doctors d ON ds.doctor_id = d.doctor_id
                       WHERE LOWER(TRIM(d.specialization)) = LOWER(TRIM(?))""",
                    conn, params=(specialist,)
                )

                if not available_doctors.empty:
                    st.dataframe(available_doctors, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No available {specialist} doctor shifts found.")

        if "last_prediction" in st.session_state:
            st.divider()
            pred = st.session_state["last_prediction"]
            pdf_bytes = generate_pdf_report(
                pred["patient_name"], pred["age"], pred["gender"], pred["phone"],
                pred["symptoms"], pred["disease"], pred["description"], pred["specialist"],
                pred.get("medicines", ""), pred.get("notes", "")
            )

            st.download_button(
                label="📥 Download Prescription PDF Report",
                data=pdf_bytes,
                file_name=f"Report_{pred['patient_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# -----------------------------
# 3. Appointments & Status Update
# -----------------------------
elif menu == "Appointments":
    st.header("📅 Appointment Booking & Status Management")
    
    col_book, col_status = st.columns([1, 1])

    with col_book:
        st.subheader("📌 Book Appointment")
        patients = pd.read_sql_query("SELECT patient_id, patient_name FROM patients", conn)
        doctors = pd.read_sql_query("SELECT doctor_id, doctor_name, specialization FROM doctors", conn)

        if not patients.empty and not doctors.empty:
            patient_options = {f"{row['patient_name']} (ID: {row['patient_id']})": row["patient_id"] for _, row in patients.iterrows()}
            selected_patient_id = patient_options[st.selectbox("👤 Select Patient", list(patient_options.keys()))]

            doctor_options = {f"{row['doctor_name']} - {row['specialization']}": row["doctor_id"] for _, row in doctors.iterrows()}
            selected_doctor_id = doctor_options[st.selectbox("👨‍⚕️ Select Doctor", list(doctor_options.keys()))]

            appointment_date = st.date_input("📅 Appointment Date")
            appointment_time = st.time_input("⏰ Appointment Time")
            reason = st.text_input("📝 Reason")

            if st.button("📅 Book Appointment"):
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, reason) VALUES (?, ?, ?, ?, ?, ?)",
                    (selected_patient_id, selected_doctor_id, appointment_date.strftime("%Y-%m-%d"), appointment_time.strftime("%H:%M"), "Booked", reason)
                )
                conn.commit()
                st.success("Appointment booked successfully!")
                st.rerun()

    with col_status:
        st.subheader("🔄 Update Appointment Status")
        appointments_df = pd.read_sql_query("SELECT appointment_id, status FROM appointments ORDER BY appointment_id DESC", conn)
        if not appointments_df.empty:
            app_id = st.selectbox("Select Appointment ID", appointments_df["appointment_id"].tolist())
            new_status = st.selectbox("Select New Status", ["Booked", "Pending", "Confirmed", "Completed", "Cancelled"])
            
            if st.button("🔄 Update Status"):
                cursor = conn.cursor()
                cursor.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?", (new_status, app_id))
                conn.commit()
                st.success(f"Appointment #{app_id} status updated to {new_status}!")
                st.rerun()

    st.divider()
    st.subheader("📋 Appointments Directory")
    appointments = pd.read_sql_query(
        """SELECT a.appointment_id, p.patient_name, d.doctor_name, d.specialization, a.appointment_date, a.appointment_time, a.status, a.reason
           FROM appointments a JOIN patients p ON a.patient_id = p.patient_id JOIN doctors d ON a.doctor_id = d.doctor_id ORDER BY a.appointment_id DESC""",
        conn
    )
    st.dataframe(appointments, use_container_width=True, hide_index=True)

# -----------------------------
# 4. Doctors & Duty Schedule
# -----------------------------
elif menu == "Doctors & Duty Schedule":
    st.header("👨‍⚕️ Doctors Directory & Duty Schedule")
    
    tab1, tab2 = st.tabs(["👨‍⚕️ Doctors List", "🕒 Duty Schedules"])
    
    with tab1:
        doctors = pd.read_sql_query("SELECT doctor_id, doctor_name, specialization, phone, email, room_number FROM doctors", conn)
        st.dataframe(doctors, use_container_width=True, hide_index=True)

    with tab2:
        shifts = pd.read_sql_query(
            """SELECT d.doctor_name, d.specialization, ds.duty_date, ds.shift_name, ds.start_time, ds.end_time, d.room_number, ds.status
               FROM doctor_shifts ds JOIN doctors d ON ds.doctor_id = d.doctor_id ORDER BY ds.duty_date DESC""",
            conn
        )
        st.dataframe(shifts, use_container_width=True, hide_index=True)

# -----------------------------
# 5. Patient Management
# -----------------------------
elif menu == "Patient Management":
    st.header("👤 Patient Registration & Registry")

    with st.expander("➕ Register New Patient"):
        with st.form("add_patient_form", clear_on_submit=True):
            p_name = st.text_input("Patient Full Name*")
            p_age = st.number_input("Age*", min_value=1, max_value=120, value=25)
            p_gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            p_phone = st.text_input("Phone Number")
            p_address = st.text_area("Address")
            p_symptoms = st.text_input("Initial Symptoms")

            if st.form_submit_button("💾 Save Patient"):
                if p_name:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO patients (patient_name, age, gender, phone, address, symptoms, registration_date) VALUES (?, ?, ?, ?, ?, ?, DATE('now'))",
                        (p_name, p_age, p_gender, p_phone, p_address, p_symptoms)
                    )
                    conn.commit()
                    st.success(f"Patient '{p_name}' successfully added!")
                    st.rerun()

    st.subheader("📋 Registered Patients")
    patients = pd.read_sql_query("SELECT patient_id, patient_name, age, gender, phone, address, symptoms, registration_date FROM patients ORDER BY patient_id DESC", conn)
    st.dataframe(patients, use_container_width=True, hide_index=True)

# -----------------------------
# 6. Patient History & Search
# -----------------------------
elif menu == "Patient History & Search":
    st.header("📜 Patient Search & Medical History")
    
    search_term = st.text_input("🔎 Search Patient by Name or Phone Number", "")
    
    if search_term:
        patient_res = pd.read_sql_query(
            "SELECT * FROM patients WHERE patient_name LIKE ? OR phone LIKE ?", 
            conn, params=(f"%{search_term}%", f"%{search_term}%")
        )
        
        if not patient_res.empty:
            st.success(f"Found {len(patient_res)} Patient(s)")
            st.dataframe(patient_res, use_container_width=True, hide_index=True)
            
            p_id = patient_res.iloc[0]["patient_id"]
            st.subheader(f"📜 Visit History for Patient ID: {p_id}")
            history = pd.read_sql_query(
                """SELECT ph.visit_date, d.doctor_name, ph.department, ph.symptoms, ph.notes 
                   FROM patient_history ph LEFT JOIN doctors d ON ph.doctor_id = d.doctor_id 
                   WHERE ph.patient_id = ? ORDER BY ph.visit_date DESC""",
                conn, params=(p_id,)
            )
            st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.warning("No records found.")
    else:
        st.info("Enter patient details above to search medical history.")

# -----------------------------
# 7. Analytics & Trends
# -----------------------------
elif menu == "Analytics & Trends":
    st.header("📈 Interactive Analytics & Hospital Trends")

    col1, col2 = st.columns(2)

    with col1:
        doctors_df = pd.read_sql_query("SELECT specialization, COUNT(*) as count FROM doctors GROUP BY specialization", conn)
        if not doctors_df.empty:
            fig1 = px.pie(doctors_df, values='count', names='specialization', title="👨‍⚕️ Doctors Specialization Distribution", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        patients_df = pd.read_sql_query("SELECT age, gender FROM patients", conn)
        if not patients_df.empty:
            fig2 = px.histogram(patients_df, x="age", color="gender", title="👥 Patient Age & Gender Demographics", nbins=10)
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📅 Appointment Trends Over Time")
    trend_df = pd.read_sql_query("SELECT appointment_date, COUNT(*) as count FROM appointments GROUP BY appointment_date ORDER BY appointment_date", conn)
    if not trend_df.empty:
        fig_trend = px.line(trend_df, x='appointment_date', y='count', title="Daily Appointment Trends", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------
# 8. Reports & Feedback
# -----------------------------
elif menu == "Reports & Feedback":
    st.header("📑 Reports & Patient Feedback")

    st.subheader("📄 Download Medical PDF Report")
    patients_df = pd.read_sql_query("SELECT patient_id, patient_name, age, gender, phone, symptoms FROM patients ORDER BY patient_name", conn)

    if not patients_df.empty:
        selected_p = st.selectbox("Select Patient", patients_df["patient_name"].tolist())
        p_row = patients_df[patients_df["patient_name"] == selected_p].iloc[0]

        rep_disease = st.text_input("Diagnosed Disease", value="General Checkup")
        rep_specialist = st.text_input("Specialist", value="General Physician")
        rep_meds = st.text_area("Prescribed Medicines", value="Paracetamol 500mg")
        rep_desc = st.text_area("Summary", value="Patient routine checkup done.")

        pdf_data = generate_pdf_report(
            p_row["patient_name"], p_row.get("age", "N/A"), p_row.get("gender", "N/A"),
            p_row.get("phone", "N/A"), p_row.get("symptoms", "None"), rep_disease, rep_desc, rep_specialist, rep_meds, rep_desc
        )

        st.download_button(
            label="📥 Download Detailed Patient PDF Report",
            data=pdf_data,
            file_name=f"Report_{p_row['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.divider()
    st.subheader("⭐ Patient Feedback Collection")
    fb_patient = st.text_input("Patient Name")
    fb_rating = st.slider("Rating", 1, 5, 5)
    fb_comments = st.text_area("Feedback Comments")

    if st.button("💬 Submit Feedback"):
        if fb_patient:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (patient_name, rating, comments) VALUES (?, ?, ?)", (fb_patient, fb_rating, fb_comments))
            conn.commit()
            st.success("Thank you! Feedback recorded in database successfully.")
        else:
            st.warning("Please enter patient name.")
