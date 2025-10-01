# 🤖 Hybrid Modular Chatbot: Flow & RAG

This project implements a conversational application with a **two-part modular architecture** offering two distinct operational modes:

1. **Flow-based Project Planner**

   * Structured conversation to gather project requirements (**Name, Type, Duration, Budget**)
   * Strict **Pydantic validation**

   **note: data for rag is web scraped and saved in FAISS

2. **RAG (Retrieval-Augmented Generation) Chatbot**

   * Open-ended **Q&A system** on *Jordan Peterson content*
   * Powered by **Groq API** and LLM

The **user selects the desired mode** at the start of the conversation.

---

## 🚀 Project Architecture & Core Logic

The application uses **FastAPI (backend)** and **Streamlit (frontend)**.
The **infrastructure layer** manages **mode switching** and routes requests to either:

* **Flow logic** (structured)
* **RAG logic** (open-ended)

### 📂 File Structure

```bash
chatbot_project/
│
├── chatbotapi/                         # Backend (FastAPI)
│   └── src/
│       └── chat/
│           ├── domain/
│           │   └── flow_definition.py        # Defines flow steps, ProjectData, Pydantic rules
│           │
│           ├── application/
│           │   └── convo/
│           │       └── response_generation.py # HybridGenerator for RAG/LLM
│           │
│           └── infrastructure/
│               └── api.py                     # FastAPI app, endpoints, session management, mode switching
│
├── chatbot_ui/                         # Frontend (Streamlit)
│   └── src/
│       └── streamlit.py                 # UI client, chat history, API calls, mode tracking
│
├── .env                                # Environment variables (Groq API Key required)
├── requirements.txt                    # Python dependencies
└── README.md                           # Project documentation (this file)
```

---

## 💻 Getting Started

### ✅ Prerequisites

* Python **3.8+**
* **Groq API Key** (required for RAG mode)

---

### 1. Setup Environment Variables

Create a `.env` file in the project root:

```ini
GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"
```

---

### 2. Setup Virtual Environment

```bash
# Create venv
python -m venv .venv

# Activate venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

Use **two terminals** (backend + frontend).

### Terminal 1: Start FastAPI Backend

```bash
uvicorn chatbotapi.src.chat.infrastructure.api:app --reload
```

Wait for:

```
Application startup complete.
```

---

### Terminal 2: Start Streamlit Frontend

```bash
# Activate venv if not already
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Run UI
streamlit run chatbot_ui/src/streamlit.py
```

Opens at 👉 [http://localhost:8501](http://localhost:8501)

---

## 🛠️ Operational Modes & Debugging

### 1. Initial Mode Selection

The bot first asks:

```
Would you like to use the Flow-based Project Planner or the Jordan Peterson RAG Chatbot?
(Respond with 'Flow' or 'RAG')
```

---

### 2. Flow-based Project Planner (Mode: `flow`)

* **Activation:** Respond with `Flow`
* **Purpose:** Collect structured project details
* **Validation (Pydantic):**

  * Name: min **3 characters**
  * Project Type: **≥ 2 words**
  * Duration / Budget: **positive integers**
* **Debugging:** Input errors → check FastAPI logs in Terminal 1

---

### 3. RAG Chatbot (Mode: `rag`)

* **Activation:** Respond with `RAG`
* **Purpose:** Open-ended **Jordan Peterson Q&A**
* **Behavior:** Remains in `rag` mode until reset
* **Debugging:**

  * If LLM fails → check `.env` and ensure `GROQ_API_KEY` is valid
  * Verify internet connection

---

## 🔄 Resetting the Session

To switch modes or restart:

* Click **"Start New Flow"** (appears after Flow completion), OR
* Call API reset endpoint:

```bash
POST http://localhost:8000/flow/reset?session_id=<your_session_id>
```

This clears the in-memory session state.

---
