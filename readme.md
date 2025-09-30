# 🧩 Modular Project Intake Chatbot

This project implements a conversational flow to gather **project requirements**:

* Name
* Project Type
* Duration
* Budget

It uses a **modular, two-part architecture**:

* **Backend (FastAPI):** Handles session management, flow progression, and strict Pydantic validation of user inputs at each step.
* **Frontend (Streamlit):** Provides a conversational UI that communicates with the FastAPI backend via HTTP requests.

---

## 🚀 Project Structure & Core Logic

The application is structured logically by layers:

| **Layer**          | **File Path**                                   | **Purpose**                                                                         |
| ------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Domain**         | `chatbotapi/src/chat/domain/flow_definition.py` | Defines conversation steps (`CHAT_FLOW`), `ProjectData`, and Pydantic rules         |
| **Infrastructure** | `chatbotapi/src/chat/infrastructure/api.py`     | FastAPI app, endpoints (`/flow/submit`, `/flow/reset`), session storage, validation |
| **UI Client**      | `chatbot_ui/src/streamlit.py`                   | Streamlit UI for chat history rendering and API communication                       |

---

## 💻 Getting Started

### Prerequisites

* Python **3.8+**

### 1. Setup Virtual Environment

It’s highly recommended to use a virtual environment for dependencies:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

With your virtual environment active, install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

The app requires **two terminals** (one for the backend, one for the frontend).

### Terminal 1: Start FastAPI Backend

```bash
uvicorn chatbotapi.src.chat.infrastructure.api:app --reload
```

Wait for: `Application startup complete.`

### Terminal 2: Start Streamlit Frontend

```bash
# Activate virtual environment (if not already active)
# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Run Streamlit
streamlit run chatbot_ui/src/streamlit.py
```

This opens the app in your browser: [http://localhost:8501](http://localhost:8501)

---

## 🛠️ Debugging Validation Errors

If you see an **Input Error** in the Streamlit UI, it means the input failed **Pydantic validation**.

### Steps to Debug

1. **Check FastAPI Logs:**
   In the terminal running `uvicorn`, Pydantic will print detailed error messages (e.g., `ValueError` from `@field_validator`).

2. **Review Input Rules:**

   * **Name:** Minimum **3 characters**
   * **Project Type:** Must be at least **two words**
   * **Duration / Budget:** Must be **positive integers**

---
