
# 💊 MediIQ – An AI-Powered Medicine Intelligence Assistant

## 📌 Project Overview

MediIQ is an AI-powered medicine intelligence assistant designed to help users access medicine-related information and manage their medication schedules.

The application provides an interactive chatbot, medicine reminders, dosage schedule management, and notification features to support better medication management.

## 🎯 Objectives

- Provide medicine-related information through an AI chatbot.
- Help users manage their medicine schedules.
- Send timely medication reminders.
- Maintain medicine dose history.
- Improve medication management through a user-friendly interface.

## ✨ Key Features

- **AI Medicine Chatbot:** Interact with MedBot to ask medicine-related questions.
- **User Authentication:** Secure user registration and login.
- **Medicine Schedule Management:** Add, edit, and manage medicine schedules.
- **Medicine Reminders:** Get reminders for scheduled medicines.
- **Dose History:** Track previously scheduled and recorded doses.
- **WhatsApp Notifications:** Receive medicine-related notifications.
- **Multi-language Support:** Language selection for a better user experience.
- **User Dashboard:** Manage medication information through a centralized dashboard.
- **Profile Management:** Manage personal account details.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | Firebase |
| AI Integration | Groq API |
| Notifications | Twilio |
| Development Tools | VS Code, Git, GitHub |

## 📂 Project Structure

```text
MedIQ-An-AI-Powered-Medicine-Intelligence-Assistant/
│
├── app.py
├── firebase_helper.py
├── requirements.txt
├── run.bat
├── Procfile
├── esp32_guide.md
│
├── Templates/
│   ├── chatbot.html
│   ├── dashboard.html
│   ├── login.html
│   ├── signup.html
│   ├── add_schedule.html
│   ├── edit_schedule.html
│   └── ...
│
└── static/
    └── style.css
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to Project Directory

```bash
cd MedIQ-An-AI-Powered-Medicine-Intelligence-Assistant
```

### 3. Create Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate Virtual Environment

Windows:

```bash
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory and configure your API credentials:

```env
GROQ_API_KEY=your_groq_api_key
TWILIO_SID=your_twilio_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_NUMBER=your_twilio_number
TWILIO_WHATSAPP=your_whatsapp_number
```

Configure Firebase credentials according to your Firebase setup.

**Note:** Never upload your `.env` file or API credentials to GitHub.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## 🔮 Future Enhancements

- Advanced medicine information retrieval.
- Improved chatbot responses.
- Enhanced medication tracking.
- Better notification management.
- Additional language support.
- Personalized medicine information assistance.

## ⚠️ Disclaimer

MediIQ is an informational and medication management application. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical decisions.

## 👩‍💻 Developed By

**Nidhi Sandbhor**

BE – Artificial Intelligence and Data Science

Savitribai Phule Pune University (SPPU)

---

⭐ If you find this project useful, consider giving it a star!
