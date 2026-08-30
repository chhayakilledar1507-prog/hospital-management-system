import streamlit as st
import pickle
import pandas as pd
import sqlite3

st.set_page_config(
    page_title="Smart Hospital Management System",
    page_icon="🏥",
    layout="wide"
)

# -----------------------------
# Load ML Model
# -----------------------------

with open("model/disease_model.pkl", "rb") as f:
    model = pickle.load(f)

# -----------------------------
# Load Vectorizer
# -----------------------------

with open("model/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# -----------------------------
# Database Connection
# -----------------------------

conn = sqlite3.connect(
    "database/hospital.db",
    check_same_thread=False
)
# -----------------------------
# Load Disease Description
# -----------------------------

disease_description = pd.read_csv(
    "data/Disease_Description.csv",
    encoding="latin1"
)

# Clean column names
disease_description.columns = [
    col.strip() for col in disease_description.columns
]


# -----------------------------
# Load Disease → Specialist
# -----------------------------

doctor_disease = pd.read_csv(
    "data/Doctor_Versus_Disease.csv",
    header=None,
    names=["Disease", "Specialist"],
    encoding="latin1"
)

doctor_disease["Disease"] = (
    doctor_disease["Disease"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

doctor_disease["Specialist"] = (
    doctor_disease["Specialist"]
    .astype(str)
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

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Disease Prediction",
        "Appointments",
        "Doctors",
        "Patients",
        "Patient History"
    ]
)


# -----------------------------
# Dashboard
# -----------------------------

if menu == "Dashboard":

    st.title("📊 Dashboard")

    total_patients = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM patients",
        conn
    ).iloc[0]["count"]

    total_doctors = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM doctors",
        conn
    ).iloc[0]["count"]

    total_appointments = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM appointments",
        conn
    ).iloc[0]["count"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👤 Total Patients", total_patients)

    with col2:
        st.metric("👨‍⚕️ Total Doctors", total_doctors)

    with col3:
        st.metric("📅 Total Appointments", total_appointments)

    st.divider()

    st.subheader("🏥 Smart Hospital Management System")

    st.write(
        """
        Welcome to the Smart Hospital Management & Recommendation System.

        This system provides:

        🔬 Disease prediction from symptoms  
        🩺 Specialist recommendation  
        👨‍⚕️ Available doctor information  
        👤 Patient management  
        📅 Appointment booking  
        📜 Patient history
        """
    )
        # -----------------------------
# Appointments
# -----------------------------

elif menu == "Appointments":

    st.header("📅 Appointment Management")

    patients = pd.read_sql_query(
        """
        SELECT patient_id, patient_name
        FROM patients
        """,
        conn
    )

    doctors = pd.read_sql_query(
        """
        SELECT doctor_id, doctor_name, specialization
        FROM doctors
        """,
        conn
    )
            # -----------------------------
    # Select Patient
    # -----------------------------

    patient_options = {
        f"{row['patient_name']} (ID: {row['patient_id']})":
        row["patient_id"]
        for _, row in patients.iterrows()
    }

    selected_patient = st.selectbox(
        "👤 Select Patient",
        list(patient_options.keys()),
        key="appointment_patient"
    )

    selected_patient_id = patient_options[selected_patient]


    # -----------------------------
    # Select Doctor
    # -----------------------------

    doctor_options = {
        f"{row['doctor_name']} - {row['specialization']}":
        row["doctor_id"]
        for _, row in doctors.iterrows()
    }

    selected_doctor = st.selectbox(
        "👨‍⚕️ Select Doctor",
        list(doctor_options.keys()),
        key="appointment_doctor"
    )

    selected_doctor_id = doctor_options[selected_doctor]

        # -----------------------------
    # Appointment Details
    # -----------------------------

    appointment_date = st.date_input(
        "📅 Appointment Date",
        key="appointment_date"
    )

    appointment_time = st.time_input(
        "⏰ Appointment Time",
        key="appointment_time"
    )

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
        # -----------------------------
# Doctors
# -----------------------------

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
    # -----------------------------
# Patients
# -----------------------------

elif menu == "Patients":

    st.header("👤 Patient Management")

    patients = pd.read_sql_query(
        """
        SELECT
            patient_id,
            patient_name,
            age,
            gender,
            phone,
            address,
            symptoms,
            registration_date
        FROM patients
        ORDER BY patient_id
        """,
        conn
    )

    st.dataframe(
        patients,
        use_container_width=True,
        hide_index=True
    )
    # -----------------------------
# Patient History
# -----------------------------

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


# =====================================
# Disease Prediction Page
# =====================================

if menu == "Disease Prediction":

    st.title("🔬 Disease Prediction")

    st.write("Select patient and symptoms for disease prediction.")

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
        "data/Symptom_Weights.csv",
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
                WHERE LOWER(TRIM(d.specialization)) = LOWER(TRIM(?))
                AND ds.duty_date = ?
                """,
                conn,
                params=(specialist, "2026-08-24")
            )

            if not available_doctors.empty:

                st.dataframe(
                    available_doctors,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    f"No available {specialist} doctors found for 2026-08-24."
                )

            # -----------------------------
            # Save Information
            # -----------------------------

            st.session_state["patient_id"] = selected_patient_id
            st.session_state["predicted_disease"] = predicted_disease
            st.session_state["specialist"] = specialist