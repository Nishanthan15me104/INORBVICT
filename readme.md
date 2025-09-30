Modular Project Intake Chatbot
This project implements a conversational flow to gather project requirements (Name, Project Type, Duration, and Budget). It uses a modular, two-part architecture:

Backend (FastAPI): Handles session management, flow progression, and strict Pydantic validation of user inputs at each step.

Frontend (Streamlit): Provides a conversational user interface (UI) that communicates with the FastAPI backend via HTTP requests.

🚀 Project Structure & Core Logic
The application is structured logically by layer:

Layer

File Path

Purpose

Domain

chatbotapi/src/chat/domain/flow_definition.py

Defines the conversation steps (CHAT_FLOW) and the required data structure (ProjectData) along with all Pydantic validation rules.

Infrastructure

chatbotapi/src/chat/infrastructure/api.py

Contains the FastAPI application, including endpoints (/flow/submit, /flow/reset), in-memory session storage, and the critical logic for single-step Pydantic validation.

UI Client

chatbot_ui/src/streamlit.py

Contains the Streamlit user interface code for rendering the chat history and managing API communication.

💻 Getting Started
Follow these steps to set up and run the application locally.

Prerequisites
You need Python 3.8+ installed on your system.

1. Setup Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.\.venv\Scripts\activate

# Activate the virtual environment (macOS/Linux)
source .venv/bin/activate

2. Install Dependencies
With your virtual environment active, install all required packages using the requirements.txt file:

# Install packages listed in the requirements.txt file
pip install -r requirements.txt

▶️ Running the Application
The application requires two separate terminals to run the API and the UI concurrently.

Terminal 1: Start the FastAPI Backend
Navigate to your project root and run the FastAPI server using uvicorn. The --reload flag enables live code reloading during development.

# Ensure you are in the project root directory
(venv) $ uvicorn chatbotapi.src.chat.infrastructure.api:app --reload

Wait until you see the message: Application startup complete.

Terminal 2: Start the Streamlit Frontend
Open a new terminal window, activate the same virtual environment, and run the Streamlit application.

# Activate the virtual environment (if not already active)
(venv) $ .\.venv\Scripts\activate # Windows
# or: source .venv/bin/activate # macOS/Linux

# Run the Streamlit client
(venv) $ streamlit run chatbot_ui/src/streamlit.py

This will automatically open the web application in your default browser, typically at http://localhost:8501.

🛠️ Debugging Validation Errors
If you encounter an Input Error message in the Streamlit UI, it means the input failed Pydantic validation:

Check the FastAPI Terminal: Look at the logs in the terminal running uvicorn. Pydantic usually prints detailed error messages (like ValueError messages from your @field_validator methods) that explain exactly why the input was rejected.

Review Input Rules:

Name: Must be at least 3 characters long.

Project Type: Must be described in at least two words.

Duration/Budget: Must be positive integers.