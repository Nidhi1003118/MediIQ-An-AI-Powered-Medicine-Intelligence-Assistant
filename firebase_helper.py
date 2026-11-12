import firebase_admin
from firebase_admin import credentials, firestore
import uuid

# 🔹 Firebase Admin SDK सुरू करा (path बरोबर टाका)
JSON_PATH = r"C:\Users\nidhi\medboxalert-a2029-firebase-adminsdk-fbsvc-40d373505c.json"
# Safe initialization
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(JSON_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print("🔥 Firebase initialization error:", e)

# Firestore client
db = firestore.client()

# -------------------------
# 👤 User functions
# -------------------------
def create_user(phone, data):
    """नवीन user तयार करा (phone हा document id आहे)"""
    try:
        doc_ref = db.collection("users").document(phone)
        if doc_ref.get().exists:
            print("⚠️ User already exists.")
            return False
        doc_ref.set(data)
        print("✅ User created:", phone)
        return True
    except Exception as e:
        print("🔥 Error creating user:", e)
        return False

def get_user(phone):
    """User fetch करा phone id वापरून"""
    try:
        doc_ref = db.collection("users").document(phone)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        print("⚠️ User not found:", phone)
        return None
    except Exception as e:
        print("🔥 Error fetching user:", e)
        return None

def update_user(phone, data):
    """Update user profile fields"""
    try:
        doc_ref = db.collection("users").document(phone)
        doc = doc_ref.get()
        if not doc.exists:
            print("⚠️ User not found for update:", phone)
            return False
        doc_ref.update(data)
        print("✅ User updated:", phone)
        return True
    except Exception as e:
        print("🔥 Error updating user:", e)
        return False

# -------------------------
# 💊 Schedule functions
# -------------------------
def create_schedule(user_phone, data):
    """नवीन schedule तयार करा unique id सह"""
    try:
        sid = str(uuid.uuid4())
        # जर total_pills असेल आणि remaining_pills नसेल तर add करा
        if "total_pills" in data and "remaining_pills" not in data:
            data["remaining_pills"] = data["total_pills"]

        db.collection("schedules").document(user_phone).collection("schedule").document(sid).set(data)
        print(f"✅ Schedule created for {user_phone} with id {sid}")
        return sid
    except Exception as e:
        print("🔥 Error creating schedule:", e)
        return None

def get_schedules(user_phone):
    """दिलेल्या user साठी सर्व schedules fetch करा"""
    try:
        docs = db.collection("schedules").document(user_phone).collection("schedule").stream()
        schedules = {}
        for doc in docs:
            schedules[doc.id] = doc.to_dict()
        return schedules
    except Exception as e:
        print("🔥 Error fetching schedules:", e)
        return {}

def update_schedule(user_phone, sid, data):
    try:
        doc_ref = db.collection("schedules") \
          .document(user_phone) \
          .collection("schedule") \
          .document(sid)

        doc_ref.update(data)

        print(f"✅ Schedule updated: {sid}")
        return True

    except Exception as e:
        print("🔥 Error updating schedule:", e)
        return False

def delete_schedule(user_phone, sid):
    """दिलेला schedule delete करा"""
    try:
        doc_ref = db.collection("schedules").document(user_phone).collection("schedule").document(sid)
        doc_ref.delete()
        print(f"🗑️ Deleted schedule {sid} for {user_phone}")
        return True
    except Exception as e:
        print("🔥 Error deleting schedule:", e)
        return False
def update_user_password(phone, new_password):
    try:
        doc_ref = db.collection("users").document(phone)
        doc = doc_ref.get()

        if not doc.exists:
            print("❌ User not found for password update")
            return False

        doc_ref.update({
            "password": new_password
        })

        print("✅ Password updated successfully for", phone)
        return True

    except Exception as e:
        print("🔥 Error updating password:", e)
        return False



# -------------------------
# ⚙️ NEW: Decrement pills
# -------------------------
def decrement_pills(user_phone, sid, amount=1):
    """
    Remaining pills ची संख्या कमी करा आणि नवीन value परत द्या.
    Example: decrement_pills("9999999999", "sid123", 2)
    """
    try:
        doc_ref = db.collection("schedules").document(user_phone).collection("schedule").document(sid)
        doc = doc_ref.get()
        if not doc.exists:
            raise Exception("Schedule not found")

        data = doc.to_dict()
        remaining = int(data.get("remaining_pills", data.get("total_pills", 0)))
        new_remaining = max(0, remaining - int(amount))

        doc_ref.update({"remaining_pills": new_remaining})
        print(f"💊 Remaining pills updated: {remaining} ➜ {new_remaining}")
        return new_remaining
    except Exception as e:
        print("🔥 Error decrementing pills:", e)
        return None
def get_all_users():
    try:
        users_ref = db.collection("users").stream()
        users = {}

        for doc in users_ref:
            users[doc.id] = doc.to_dict()

        return users
    except Exception as e:
        print("Error fetching all users:", e)
        return {}
def delete_user(phone):
    try:
        doc_ref = db.collection("users").document(phone)
        doc = doc_ref.get()

        if not doc.exists:
            print("⚠️ User not found for deletion")
            return False

        doc_ref.delete()
        print("🗑️ User deleted:", phone)
        return True

    except Exception as e:
        print("🔥 Delete user error:", e)
        return False

def delete_user_schedules(phone):
    try:
        schedules_ref = db.collection("schedules") \
                          .document(phone) \
                          .collection("schedule") \
                          .stream()

        for doc in schedules_ref:
            doc.reference.delete()

        print("🗑️ All schedules deleted for", phone)
        return True

    except Exception as e:
        print("🔥 Delete schedules error:", e)
        return False


def delete_user_schedules(phone):
    try:
        schedules = db.collection("schedules") \
                      .document(phone) \
                      .collection("schedule") \
                      .stream()

        deleted = 0
        for doc in schedules:
            doc.reference.delete()
            deleted += 1

        print(f"🗑️ Deleted {deleted} schedules for {phone}")
        return True

    except Exception as e:
        print("🔥 Delete schedules error:", e)
        return False



# -------------------------
# ✅ Debug / Test
# -------------------------
if __name__ == "__main__":
    test_user = {"name": "Test User", "password": "1234"}
    create_user("9999999999", test_user)

    # Test Schedule
    schedule = {
        "name": "Paracetamol",
        "dose": "1 Tablet",
        "total_pills": 10,
        "remaining_pills": 10
    }
    sid = create_schedule("9999999999", schedule)

    # Show all schedules
    scheds = get_schedules("9999999999")
    print("📦 Schedules:", scheds)

    # Test decrement
    if sid:
        new_val = decrement_pills("9999999999", sid, 2)
        print("After decrement:", new_val)