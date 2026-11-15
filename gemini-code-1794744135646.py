import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-saas-demo-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital_saas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Multi-Tenant Models ---
class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    plan = db.Column(db.String(50), default="Pro SaaS")

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(200), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default="Scheduled")

# --- Seed Demo Data ---
def seed_demo_data():
    if Hospital.query.first():
        return
    h1 = Hospital(name="Apollo Metro Care", plan="Enterprise")
    h2 = Hospital(name="Sunrise Community Clinic", plan="Starter")
    db.session.add_all([h1, h2])
    db.session.commit()

    db.session.add_all([
        Patient(hospital_id=h1.id, name="Aarav Sharma", age=34, condition="Hypertension Follow-up"),
        Patient(hospital_id=h1.id, name="Meera Nair", age=28, condition="Post-Op Orthopedic Check"),
        Patient(hospital_id=h2.id, name="David Miller", age=52, condition="Routine Cardiac Screening"),
        Appointment(hospital_id=h1.id, patient_name="Aarav Sharma", doctor_name="Dr. Priya Menon", department="Cardiology", date="2026-11-16", status="Confirmed"),
        Appointment(hospital_id=h2.id, patient_name="David Miller", doctor_name="Dr. John Carter", department="General Medicine", date="2026-11-17", status="Scheduled"),
    ])
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_demo_data()

# --- Routes ---
@app.route("/")
def dashboard():
    hospitals = Hospital.query.all()
    current_id = session.get("hospital_id", hospitals[0].id)
    current_hospital = db.session.get(Hospital, current_id) or hospitals[0]

    patients = Patient.query.filter_by(hospital_id=current_hospital.id).all()
    appointments = Appointment.query.filter_by(hospital_id=current_hospital.id).all()

    return render_template(
        "index.html",
        hospitals=hospitals,
        current_hospital=current_hospital,
        patients=patients,
        appointments=appointments,
    )

@app.route("/switch-tenant/<int:hospital_id>")
def switch_tenant(hospital_id):
    session["hospital_id"] = hospital_id
    return redirect(url_for("dashboard"))

@app.route("/add-patient", methods=["POST"])
def add_patient():
    hospital_id = session.get("hospital_id", 1)
    new_patient = Patient(
        hospital_id=hospital_id,
        name=request.form["name"],
        age=int(request.form["age"]),
        condition=request.form["condition"],
    )
    db.session.add(new_patient)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/add-appointment", methods=["POST"])
def add_appointment():
    hospital_id = session.get("hospital_id", 1)
    new_appt = Appointment(
        hospital_id=hospital_id,
        patient_name=request.form["patient_name"],
        doctor_name=request.form["doctor_name"],
        department=request.form["department"],
        date=request.form["date"],
    )
    db.session.add(new_appt)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/complete-appointment/<int:appt_id>")
def complete_appointment(appt_id):
    appt = db.session.get(Appointment, appt_id)
    if appt:
        appt.status = "Completed"
        db.session.commit()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)