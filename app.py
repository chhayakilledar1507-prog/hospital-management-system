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
    "Doctor_Versus_Disease.csv",s st
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
