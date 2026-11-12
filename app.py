import os
from dotenv import load_dotenv
load_dotenv()
import requests
from deep_translator import GoogleTranslator
from flask import Flask, render_template, request, redirect, session, jsonify
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from firebase_helper import (
    create_user,
    get_user,
    update_user,
    update_user_password,
    get_schedules,
    create_schedule,
    delete_user,
    delete_user_schedules,
    update_schedule,
    delete_schedule,
    decrement_pills,
    get_all_users
)
import google.generativeai as genai
from twilio.rest import Client
import random
from datetime import datetime
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "medbox_secret")
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)

LANG = {

    "en":{
    "hello":"Hello",
    "stay":"Stay strong! Every dose counts.",
    "add_med":"Add Medicine",
    "name":"Medicine Name",
    "dose":"Dose",
    "total_pills":"Total Pills",
    "medicine_type":"Medicine Type",
    "select_type":"Select Type",
    "tablet":"Tablet",
    "syrup":"Syrup",
    "schedule":"Schedule",
    "start_date":"Start Date",
    "end_date":"End Date",
    "expiry_date":"Expiry Date",
    "food_instruction":"Food Instruction",
    "before_food":"Before Food",
    "after_food":"After Food",
    "frequency":"Frequency",
    "daily":"Daily",
    "weekly":"Weekly",
    "timing":"Timing",
    "times_day":"How many times a day?",
    "save":"Save",
    "dashboard":"Dashboard",
    "edit":"Edit",
    "delete":"Delete",
    "fill_details":"Fill in the details for your medication"
    },

    "mr":{
    "hello":"नमस्कार",
    "stay":"मजबूत रहा! प्रत्येक डोस महत्वाचा आहे.",
    "add_med":"औषध जोडा",
    "name":"औषधाचे नाव",
    "dose":"डोस",
    "total_pills":"एकूण गोळ्या",
    "medicine_type":"औषध प्रकार",
    "select_type":"प्रकार निवडा",
    "tablet":"गोळी",
    "syrup":"सिरप",
    "schedule":"वेळापत्रक",
    "start_date":"सुरुवात तारीख",
    "end_date":"समाप्ती तारीख",
    "expiry_date":"कालबाह्यता तारीख",
    "food_instruction":"अन्न सूचना",
    "before_food":"जेवणाआधी",
    "after_food":"जेवणानंतर",
    "frequency":"वारंवारता",
    "daily":"दररोज",
    "weekly":"आठवड्यातून",
    "timing":"वेळ",
    "times_day":"दिवसात किती वेळा?",
    "save":"सेव्ह करा",
    "dashboard":"डॅशबोर्ड",
    "edit":"संपादित करा",
    "delete":"हटवा",
    "fill_details":"तुमच्या औषधाची माहिती भरा"
    },

    "hi":{
    "hello":"नमस्ते",
    "stay":"मजबूत रहें! हर डोज़ मायने रखता है.",
    "add_med":"दवा जोड़ें",
    "name":"दवा का नाम",
    "dose":"डोज़",
    "total_pills":"कुल गोलियां",
    "medicine_type":"दवा प्रकार",
    "select_type":"प्रकार चुनें",
    "tablet":"गोली",
    "syrup":"सिरप",
    "schedule":"शेड्यूल",
    "start_date":"शुरू तिथि",
    "end_date":"समाप्ति तिथि",
    "expiry_date":"समाप्ति तिथि",
    "food_instruction":"भोजन निर्देश",
    "before_food":"भोजन से पहले",
    "after_food":"भोजन के बाद",
    "frequency":"आवृत्ति",
    "daily":"दैनिक",
    "weekly":"साप्ताहिक",
    "timing":"समय",
    "times_day":"दिन में कितनी बार?",
    "save":"सेव करें",
    "dashboard":"डैशबोर्ड",
    "edit":"संपादित करें",
    "delete":"हटाएं",
    "fill_details":"अपनी दवा का विवरण भरें"
    }

}
# ========= TRANSLATE FUNCTION =========
def translate_text(text, lang):
    try:
        if lang == "en":
            return text
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except:
        return text


def parse_iso(dt_str):
    """Parse ISO datetime strings robustly."""
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def get_reminder_ui(med):
    now = datetime.now()
    status = med.get("medicine_status", {}) or {}
    state = status.get("state", "idle")
    expires_at = parse_iso(status.get("expires_at", ""))

    if state == "pending":
        window_start = parse_iso(status.get("window_start", ""))
        if expires_at and window_start and window_start <= now <= expires_at:
            return {
                "state": "pending",
                "active_time": status.get("active_time", ""),
                "attempt": status.get("attempt", 1),
                "expires_at": expires_at.strftime("%I:%M %p") if expires_at else "",
                "show_button": True,
                "status_label": f"Take by {expires_at.strftime('%I:%M %p')}" if expires_at else "Take now"
            }

        if expires_at and now > expires_at:
            if status.get("attempt", 1) >= 2:
                return {
                    "state": "missed",
                    "show_button": False,
                    "status_label": "Missed"
                }
            return {
                "state": "expired",
                "show_button": False,
                "status_label": "Reminder expired"
            }

    if state == "taken":
        taken_at = status.get("taken_at", "")
        return {
            "state": "taken",
            "show_button": False,
            "taken_at": taken_at,
            "status_label": f"Taken at {taken_at if taken_at else 'now'}"
        }

    if state == "missed":
        return {
            "state": "missed",
            "show_button": False,
            "status_label": "Missed"
        }

    return {
        "state": "idle",
        "show_button": False,
        "status_label": "No active reminder"
    }


# ========= TWILIO CONFIG =========
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP")

client = None

if TWILIO_SID and TWILIO_AUTH:
    client = Client(TWILIO_SID, TWILIO_AUTH)
# ========= LANGUAGE TRANSLATION =========

@app.route("/set_language/<lang>")
def set_language(lang):

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]

    update_user(phone, {"language": lang})

    return redirect("/dashboard")
    
def clean_phone(number):
    """Normalize phone: strip spaces, remove +91 or 0 prefix, return 10-digit number."""
    number = str(number).strip().replace(" ", "")
    if number.startswith("+91"):
        number = number[3:]
    elif number.startswith("91") and len(number) == 12:
        number = number[2:]
    elif number.startswith("0") and len(number) == 11:
        number = number[1:]
    return number

def send_sms(to_number, message):
    try:
        number = clean_phone(to_number)
        result = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to="+91" + number
        )
        print(f"✅ SMS sent to +91{number} | SID: {result.sid}")
        return True
    except Exception as e:
        print(f"🔥 SMS failed to {to_number}: {e}")
        return False

def send_whatsapp(to_number, message):
    try:
        number = clean_phone(to_number)
        result = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP,
            to="whatsapp:+91" + number
        )
        print(f"✅ WhatsApp sent to +91{number} | SID: {result.sid}")
        return True
    except Exception as e:
        print(f"🔥 WhatsApp failed to {to_number}: {e}")
        return False

# ========= WELCOME =========
@app.route("/")
def welcome():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("welcome.html")

# ========= LOGIN PAGE =========
@app.route("/login_page")
def login_page():

    # If user already logged in AND coming from Add Account
    if request.args.get("add") == "true":
        return render_template("login.html")

    # If already logged in normally → go dashboard
    if "user" in session:
        return redirect("/dashboard")

    return render_template("login.html")

# ========= LOGIN =========
@app.route("/login", methods=["POST"])
def login():

    phone = request.form.get("phone")
    password = request.form.get("password")

    user = get_user(phone)

    if not user:
        return "<script>alert('User not found'); window.location.href='/login_page';</script>"

    if user.get("password") != password:
        return "<script>alert('Incorrect Password'); window.location.href='/login_page';</script>"

    if "accounts" not in session:
        session["accounts"] = []

    if phone not in session["accounts"]:
        session["accounts"].append(phone)

    session.permanent = True
    session["user"] = phone

    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]

    user = get_user(phone)

    schedules = get_schedules(phone) or {}

    # Compute UI reminder state for each schedule
    last_taken = None
    last_taken_schedule = None
    for sid, med in schedules.items():
        med["reminder_ui"] = get_reminder_ui(med)
        status = med.get("medicine_status", {}) or {}
        if status.get("state") == "taken" and status.get("taken_at"):
            taken_at = parse_iso(status.get("taken_at"))
            if taken_at and (last_taken is None or taken_at > last_taken):
                last_taken = taken_at
                last_taken_schedule = med.get("name", "medication")

    if last_taken is not None:
        last_taken_text = f"Last dose: {last_taken_schedule} at {last_taken.strftime('%d %b %Y %I:%M %p')}"
    else:
        last_taken_text = "No recent dose taken yet."

    texts = get_texts()

    return render_template(
        "dashboard.html",
        name=user.get("name"),
        schedules=schedules,
        theme=session.get("theme","dark"),
        texts=texts,
        last_taken_text=last_taken_text
    )

@app.route("/dose_history")
def dose_history():
    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    schedules = get_schedules(phone) or {}
    records = []
    for sid, med in schedules.items():
        status = med.get("medicine_status", {}) or {}
        state = status.get("state")
        if state not in ["taken", "missed"]:
            continue

        ts = status.get("taken_at") if state == "taken" else status.get("missed_at")
        dt = parse_iso(ts) if ts else None
        records.append({
            "name": med.get("name", "Medicine"),
            "state": state.capitalize(),
            "time": dt.strftime("%d %b %Y %I:%M %p") if dt else "Unknown",
            "dose": med.get("dose", "")
        })

    records = sorted(records, key=lambda x: x["time"], reverse=True)
    texts = get_texts()
    return render_template("dose_history.html", records=records, texts=texts)

@app.route("/toggle_theme")
def toggle_theme():

    if "theme" not in session:
        session["theme"] = "dark"

    if session["theme"] == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect("/dashboard")

# ========= ADD SCHEDULE PAGE =========
@app.route("/add_schedule_page")
def add_schedule_page():

    if "user" not in session:
        return redirect("/login_page")

    texts = get_texts()

    return render_template("add_schedule.html", texts=texts)

# ========= ADD SCHEDULE =========
@app.route("/add_schedule", methods=["POST"])
def add_schedule():

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]

    name = request.form.get("name")
    dose = request.form.get("dose")
    start = request.form.get("start")
    end = request.form.get("end")
    expiry = request.form.get("expiry")
    total_pills = int(request.form.get("total_pills"))
    food = request.form.get("food")
    frequency = request.form.get("frequency")
    medicine_type = request.form.get("medicine_type")
    compartment = request.form.get("compartment", "")
    times_count = int(request.form.get("times_count"))
    compartments = request.form.getlist("compartments")
    if not compartments and compartment:
        compartments = [compartment]

    times = []

    for i in range(1, times_count + 1):
        hour = request.form.get(f"hour{i}")
        minute = request.form.get(f"minute{i}")
        ampm = request.form.get(f"ampm{i}")

        if hour and minute and ampm:
            times.append(f"{hour}:{minute} {ampm}")

    data = {
        "name": name,
        "dose": dose,
        "start": start,
        "end": end,
        "expiry": expiry,
        "total_pills": total_pills,
        "remaining_pills": total_pills,
        "food": food,
        "frequency": frequency,
        "medicine_type": medicine_type,
        "compartment": compartment,
        "times": times,
        "compartments": compartments,
        "last_sent": "",
        "medicine_status": {}
    }

    create_schedule(phone, data)
    
    # 🔵 Instant WhatsApp Confirmation
    #msg = f"✅ MedBox: New schedule added for *{name}* ({dose}). Reminders are set!"
    #send_whatsapp(phone, msg)

    return redirect("/dashboard")

# ========= EDIT =========
@app.route("/edit_schedule/<sid>")
def edit_schedule_page(sid):

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    schedules = get_schedules(phone)
    med = schedules.get(sid)

    texts = get_texts()

    return render_template("edit_schedule.html", sid=sid, med=med, texts=texts)

@app.route("/update_schedule/<sid>", methods=["POST"])
def update_schedule_route(sid):

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]

    from firebase_helper import update_schedule

    times_count = int(request.form.get("times_count"))
    times = []

    for i in range(1, times_count + 1):

        hour = request.form.get(f"hour{i}", "").strip()
        minute = request.form.get(f"minute{i}", "").strip()
        ampm = request.form.get(f"ampm{i}", "").strip()

        if hour and minute and ampm:
            time_value = f"{hour}:{minute} {ampm}"
            times.append(time_value)

    existing = get_schedules(phone).get(sid, {})
    compartment = request.form.get("compartment", "")
    compartments = request.form.getlist("compartments")
    if not compartments and compartment:
        compartments = [compartment]
    data = {
        "name": request.form.get("name"),
        "dose": request.form.get("dose"),
        "start": request.form.get("start"),
        "end": request.form.get("end"),
        "expiry": request.form.get("expiry"),
        "total_pills": int(request.form.get("total_pills")),
        "remaining_pills": int(request.form.get("total_pills")) if existing.get("remaining_pills") is None else existing.get("remaining_pills"),
        "food": request.form.get("food"),
        "frequency": request.form.get("frequency"),
        "medicine_type": request.form.get("medicine_type"),
        "compartment": compartment,
        "times": times,
        "compartments": compartments,
        "last_sent": existing.get("last_sent", ""),
        "medicine_status": existing.get("medicine_status", {})
    }

    update_schedule(phone, sid, data)
    
    # 🔵 Instant WhatsApp Confirmation
    #msg = f"✅ MedBox: Schedule updated for *{data['name']}*."
    #send_whatsapp(phone, msg)

    return redirect("/dashboard")

@app.route("/take_medicine/<sid>", methods=["POST"])
def take_medicine(sid):
    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    schedules = get_schedules(phone) or {}
    med = schedules.get(sid)
    if not med:
        return "<script>alert('Schedule not found'); window.location.href='/dashboard';</script>"

    status = med.get("medicine_status", {}) or {}
    if status.get("state") != "pending":
        return "<script>alert('No active medicine window.'); window.location.href='/dashboard';</script>"

    expires_at = parse_iso(status.get("expires_at", ""))
    if not expires_at or datetime.now() > expires_at:
        return "<script>alert('Reminder window expired.'); window.location.href='/dashboard';</script>"

    status["state"] = "taken"
    status["taken_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    status["show_button"] = False
    med["medicine_status"] = status
    update_schedule(phone, sid, {"medicine_status": status})

    # Decrement pills by 1 (if available)
    decrement_pills(phone, sid, 1)

    return redirect("/dashboard")

# ========= DELETE =========
@app.route("/delete_schedule/<sid>")
def delete_schedule_route(sid):

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    delete_schedule(phone, sid)

    return redirect("/dashboard")

# ========= SWITCH ACCOUNT =========
@app.route("/switch/<phone>")
def switch_account(phone):

    if "accounts" in session and phone in session["accounts"]:
        session["user"] = phone

    return redirect("/dashboard")

# ========= LOGOUT =========
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login_page")

# ========= DELETE ACCOUNT =========
@app.route("/delete_account")
def delete_account():

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]

    delete_user_schedules(phone)
    delete_user(phone)

    session.clear()

    return "<script>alert('Account Deleted Successfully'); window.location.href='/login_page';</script>"

# ========= SIGNUP =========
@app.route("/signup_page")
def signup_page():

    if request.args.get("add") == "true":
        return render_template("signup.html")

    if "user" in session:
        return redirect("/dashboard")

    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():

    phone = request.form.get("phone")

    if get_user(phone):
        return "<script>alert('User already exists'); window.location.href='/signup_page';</script>"

    password = request.form.get("password")
    confirm = request.form.get("confirm_password")

    if password != confirm:
        return "<script>alert('Passwords do not match'); window.location.href='/signup_page';</script>"

    data = {
    "name": request.form.get("name"),
    "username": request.form.get("username"),
    "email": request.form.get("email"),
    "phone": phone,
    "dob": request.form.get("dob"),
    "blood_group": request.form.get("blood_group"),
    "disease": request.form.get("disease"),
    "password": password,
    "language": request.form.get("language","en")
}
    create_user(phone, data)

    return "<script>alert('Registered Successfully'); window.location.href='/login_page';</script>"

# ========= ACCOUNT OPTIONS PAGE =========
@app.route("/account_options")
def account_options():
    return render_template("account_options.html")

# ========= FORGOT =========
@app.route("/forgot_page")
def forgot_page():
    return render_template("forgot.html")

@app.route("/forgot", methods=["POST"])
def forgot():

    phone = request.form.get("phone")
    user = get_user(phone)

    if not user:
        return "<script>alert('User not found'); window.location.href='/forgot_page';</script>"

    otp = str(random.randint(1000, 9999))
    session["otp"] = otp
    session["reset_phone"] = phone

    send_sms(phone, f"Your MedBox OTP is {otp}")

    return redirect("/verify")

@app.route("/verify")
def verify():
    return render_template("verify.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    if request.form.get("otp") != session.get("otp"):
        return "<script>alert('Invalid OTP'); window.location.href='/verify';</script>"

    return redirect("/new_password")

@app.route("/new_password")
def new_password():
    return render_template("new_password.html")

@app.route("/set_password", methods=["POST"])
def set_password():

    phone = session.get("reset_phone")
    new_pass = request.form.get("new_password")
    confirm = request.form.get("confirm_password")

    if new_pass != confirm:
        return "<script>alert('Passwords do not match'); window.history.back();</script>"

    user = get_user(phone)

    if new_pass == user.get("password"):
        return "<script>alert('New password cannot be same as old password'); window.history.back();</script>"

    update_user_password(phone, new_pass)
    session.clear()

    return "<script>alert('Password Updated Successfully'); window.location.href='/login_page';</script>"

# ========= PROFILE =========
@app.route("/profile")
def profile_page():

    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    user = get_user(phone)

    texts = get_texts()

    if not user:
        return redirect("/login_page")

    return render_template("profile.html", user=user, phone=phone, texts=texts)

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect("/login_page")
    phone = session["user"]
    data = {
        "name": request.form.get("name"),
        "username": request.form.get("username"),
        "email": request.form.get("email"),
        "dob": request.form.get("dob"),
        "blood_group": request.form.get("blood_group"),
        "disease": request.form.get("disease")
    }
    update_user(phone, data)
    return "<script>alert('Profile Updated Successfully'); window.location.href='/profile';</script>"

# ========= CHATBOT =========
@app.route("/chatbot")
def chatbot_page():

    if "user" not in session:
        return redirect("/login_page")

    texts = get_texts()

    return render_template("chatbot.html", texts=texts)

@app.route("/chat_message", methods=["POST"])
def chat_message():

    print("[MedBot] /chat_message endpoint called")

    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_msg = request.json.get("message", "")

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # Get user language
    user = get_user(session["user"])
    lang = user.get("language", "en")

    # Use Groq API for LLM response
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    return jsonify({
        "error": "Groq API key is not configured"
    }), 500

    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "system",
                "content": f"You are MedBot, a helpful medical assistant. Reply in {lang}. Keep answers short (2-4 sentences). Always remind users to consult a doctor for medical advice."
            },
            {
                "role": "user",
                "content": user_msg
            }
        ]
    }

    try:

        response = requests.post(url, headers=headers, json=data, timeout=15)

        print("[Groq API status]", response.status_code)
        print("[Groq API raw response]", response.text)

        response.raise_for_status()

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

    except Exception as e:

        print("🔥 Groq API error:", e)

        if 'response' in locals():
            print("[Groq API error response]", response.text)

        reply = "Sorry, I couldn't process your request right now. Please try again."

    return jsonify({"reply": reply})
# ========= ESP32 API =========
@app.route("/api/schedules/<phone>")
def api_get_schedules(phone):
    """ESP32 calls this to get medication schedules"""
    user = get_user(phone)
    if not user:
        return jsonify({"error": "User not found"}), 404
    schedules = get_schedules(phone) or {}
    return jsonify({"user": user.get("name"), "schedules": schedules})

@app.route("/api/dispense/<phone>/<sid>", methods=["POST"])
def api_dispense(phone, sid):
    """ESP32 calls this after dispensing pills"""
    amount = request.json.get("amount", 1) if request.is_json else 1
    new_remaining = decrement_pills(phone, sid, amount)
    if new_remaining is not None:
        return jsonify({"success": True, "remaining_pills": new_remaining})
    return jsonify({"error": "Failed to update"}), 400

def check_all_reminders():
    try:
        users = get_all_users()

        for phone in users:
            try:
                schedules = get_schedules(phone) or {}
                for sid, schedule in schedules.items():
                    send_medicine_reminder(phone, sid, schedule)
            except Exception as e:
                print(f"🔥 Error processing reminders for {phone}: {e}")

    except Exception as e:
        print(f"🔥 check_all_reminders error: {e}")

def send_medicine_reminder(phone, sid, schedule):

    now = datetime.now()
    today_date = now.date()

    try:
        start_str = schedule.get("start", "")
        end_str = schedule.get("end", "")
        if not start_str or not end_str:
            if phone != "9999999999":
                print(f"⚠️ Skipping reminder for {phone}: Missing start/end date.")
            return
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except Exception as e:
        if phone != "9999999999":
            print(f"🔥 Date error for {phone}: {e}")
        return

    if not (start_date <= today_date <= end_date):
        return

    for t in schedule.get("times", []):
        try:
            schedule_time = datetime.strptime(t, "%I:%M %p")
        except Exception as e:
            print(f"⚠️ Invalid time format for schedule {sid} time '{t}': {e}")
            continue

        schedule_time_today = now.replace(
            hour=schedule_time.hour,
            minute=schedule_time.minute,
            second=0,
            microsecond=0
        )

        first_window_start = schedule_time_today
        first_window_end = schedule_time_today + timedelta(minutes=10)
        second_window_end = schedule_time_today + timedelta(minutes=20)

        active = schedule.get("medicine_status", {}) or {}
        state = active.get("state", "idle")
        active_time = active.get("active_time")
        attempt = int(active.get("attempt", 0))

        # If this time was already taken or missed, skip
        if active_time == t and state in ["taken", "missed"]:
            continue

        # If current window still active or upcoming
        if first_window_start <= now < first_window_end:
            # Start first reminder if not already pending for this time
            if active_time != t or state != "pending":
                medicine = schedule.get('name', 'your medicine')
                dose = schedule.get('dose', '')
                message = f"""💊 It's time to take {medicine} ({dose}).\n\nPlease check the box in MedBox to confirm you've taken it within 10 minutes."""
                user = get_user(phone)
                lang = user.get("language", "en")
                message = translate_text(message, lang)
                print(f"⏰ Sending first reminder for {phone} schedule {sid} at {t}")
                send_sms(phone, message)
                send_whatsapp(phone, message)

                active = {
                    "active_time": t,
                    "state": "pending",
                    "window_start": first_window_start.isoformat(),
                    "expires_at": first_window_end.isoformat(),
                    "attempt": 1
                }
                schedule["medicine_status"] = active
                schedule["last_sent"] = first_window_start.strftime("%Y-%m-%d %H:%M")
                update_schedule(phone, sid, schedule)
            continue

        # Handle second window reminders
        if first_window_end <= now < second_window_end:
            if active_time == t and state == "pending" and attempt == 1:
                medicine = schedule.get('name', 'your medicine')
                dose = schedule.get('dose', '')
                message = f"""💊 Second Reminder: Please take {medicine} ({dose}) now and mark as taken in the app within 10 minutes."""
                user = get_user(phone)
                lang = user.get("language", "en")
                message = translate_text(message, lang)
                print(f"⏰ Sending second reminder for {phone} schedule {sid} at {t}")
                send_sms(phone, message)
                send_whatsapp(phone, message)

                active["attempt"] = 2
                active["expires_at"] = second_window_end.isoformat()
                schedule["medicine_status"] = active
                update_schedule(phone, sid, schedule)
            continue

        # Mark missed after second window
        if now >= second_window_end and active_time == t and state == "pending":
            active["state"] = "missed"
            active["missed_at"] = now.strftime("%Y-%m-%d %H:%M")
            schedule["medicine_status"] = active
            update_schedule(phone, sid, schedule)
            print(f"⚠️ Marked missed for {phone} schedule {sid} at {t}")
            continue

# ========= TEST SMS/WHATSAPP =========
@app.route("/test_sms")
def test_sms():
    if "user" not in session:
        return redirect("/login_page")

    phone = session["user"]
    msg = "✅ MedBox Test Message: SMS & WhatsApp are working!"

    sms_ok = send_sms(phone, msg)
    wa_ok = send_whatsapp(phone, msg)

    result = []
    result.append(f"SMS to +91{phone}: {'✅ Sent' if sms_ok else '❌ Failed (check console)'}")
    result.append(f"WhatsApp to +91{phone}: {'✅ Sent' if wa_ok else '❌ Failed (check console)'}")

    return "<br>".join(result) + "<br><br><a href='/dashboard'>← Back to Dashboard</a>"

# ========= DEBUG REMINDERS =========
@app.route("/debug_reminders")
def debug_reminders():
    """Manually trigger the reminder loop and return logs"""
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        print(f"--- Manual Trigger at {datetime.now()} ---")
        check_all_reminders()
    
    logs = f.getvalue()
    return f"<h1>Reminder Debug Logs</h1><pre>{logs}</pre><br><a href='/dashboard'>← Back to Dashboard</a>"

scheduler = BackgroundScheduler()
scheduler.add_job(check_all_reminders, 'interval', minutes=1)
scheduler.start()

def get_texts():

    if "user" not in session:
        return LANG["en"]

    phone = session["user"]

    user = get_user(phone)

    lang = user.get("language","en")

    return LANG.get(lang, LANG["en"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(debug=True, host=host, port=port, use_reloader=False)
