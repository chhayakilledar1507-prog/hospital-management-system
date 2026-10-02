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
# Advanced PDF Report & Prescription Generator
# -----------------------------
def generate_pdf_report(patient_name, age, gender, phone, symptoms, disease, description, specialist, medicines="", doctor_notes=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Title & Header
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#0D3B66"),
        alignment=1,
        spaceAfter=15
    )
    story.append(Paragraph("🏥 SMART HOSPITAL MEDICAL REPORT & PRESCRIPTION", header_style))
    story.append(Spacer(1, 10))

    # Patient Details Section
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

    # Diagnostic Details
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
