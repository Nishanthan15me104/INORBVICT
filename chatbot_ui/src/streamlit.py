# --- UI Layer: Streamlit Entry Point (Client Side) ---
import streamlit as st
import requests
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000"

def initialize_session_state():
    """Initializes Streamlit state and triggers the first API call."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'is_complete' not in st.session_state:
        st.session_state.is_complete = False
    if 'summary_data' not in st.session_state:
        st.session_state.summary_data = None
    if 'mode' not in st.session_state: # <-- ADDED for tracking mode
        st.session_state.mode = 'initial'
        
    # Get the initial bot message if history is empty
    if not st.session_state.history:
        # Pass a flag to indicate this is the initial, non-user triggered call
        make_api_call("", initial_call=True) 


def make_api_call(user_input: str, initial_call: bool = False):
    """Makes an HTTP POST request to FastAPI and updates Streamlit state."""
    
    # Do not proceed if flow is complete AND we are in flow mode, unless it's the initial call
    if st.session_state.is_complete and st.session_state.mode == 'flow' and not initial_call:
        return
    
    payload = {
        "session_id": st.session_state.session_id,
        "user_input": user_input,
    }
    
    # 1. Add user message to history before sending (if it's not the initial call)
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})

    try:
        response = requests.post(f"{API_BASE_URL}/flow/submit", json=payload)
        
        # Check for HTTP errors (4xx or 5xx status codes)
        if response.status_code >= 400:
            st.error(f"API HTTP Error {response.status_code}: Could not process request. Check FastAPI console for tracebacks.")
            # Remove the user message added earlier, as the submission failed
            if user_input:
                st.session_state.history.pop()
            return

        api_response = response.json()
        
        # Check for FastAPI-defined validation error status
        if api_response.get("status") == "validation_error":
            # Display validation error and do NOT rerun or advance step
            error_message = api_response.get("bot_message", "Input Error: Please try again.")
            st.error(error_message)
            # Remove the user message added earlier, as the submission failed validation
            if user_input:
                st.session_state.history.pop()
            return
            
        # 2. Update State on Success
        bot_message = api_response.get("bot_message", "An unexpected error occurred.")
        st.session_state.is_complete = api_response.get("is_complete", False)
        st.session_state.mode = api_response.get("mode", "initial") # <-- ADDED: Update mode
        
        st.session_state.history.append({"role": "assistant", "content": bot_message})
        
        if st.session_state.is_complete and st.session_state.mode == 'flow':
            st.session_state.summary_data = api_response.get("data", {})
        
        # Only rerun if it was a user-triggered input OR the initial call successfully added the first bot message
        if user_input or initial_call:
            st.rerun() # <-- Updated to st.rerun()
            
    except requests.exceptions.ConnectionError:
        # CRITICAL FIX: Removed st.stop() to allow the error message to render
        st.error(f"🚨 Connection Error: Ensure the FastAPI server is running at {API_BASE_URL}")
    except Exception as e:
        st.error(f"An unexpected error occurred in the Streamlit client: {e}")
        if user_input:
            st.session_state.history.pop()

def reset_flow_state():
    """Resets the state both on the client (Streamlit) and the server (FastAPI)."""
    try:
        requests.post(f"{API_BASE_URL}/flow/reset?session_id={st.session_state.session_id}")
    except:
        # Ignore reset errors if API is offline
        pass 
        
    st.session_state.history = []
    st.session_state.is_complete = False
    st.session_state.summary_data = None
    st.session_state.mode = 'initial' # <-- ADDED: Reset mode
    
    initialize_session_state() 
    st.rerun() # <-- Updated to st.rerun()
    
def display_flow_summary():
    """Renders the final project summary card, only called for Flow mode."""
    answers = st.session_state.summary_data
    
    st.success("🎉 Flow Complete! Summary Generated 🎉")
    st.subheader("Project Intake Summary")
    
    col1, col2 = st.columns(2)
    
    def format_currency(value):
        try:
            return f"${int(value):,}"
        except:
            return f"${value}"
            
    summary_data = [
        ("Client Name", answers.get('name', 'N/A'), col1),
        ("Project Type", answers.get('projectType', 'N/A'), col2),
        ("Estimated Duration", f"{answers.get('duration', 'N/A')} weeks", col1),
        ("Approximate Budget", format_currency(answers.get('budget', 'N/A')), col2),
    ]

    for label, value, col in summary_data:
        with col:
            st.metric(label=label, value=value)
            
    st.button("Start New Flow", on_click=reset_flow_state, use_container_width=True)

def main_app():
    """The main Streamlit application function."""
    
    st.set_page_config(page_title="Modular Chatbot", layout="centered")
    st.title("🤖 Modular Project Bot")
    
    initialize_session_state()
    
    # Display History
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle completion or continue
    # Only show the summary if we are in FLOW mode AND the flow is complete
    is_flow_complete = st.session_state.is_complete and st.session_state.mode == 'flow'
    
    if is_flow_complete:
        display_flow_summary()
        placeholder = "Flow complete! Click 'Start New Flow' to begin again."
    else:
        # RAG mode is continuous, Flow mode requires input, Initial mode requires selection
        placeholder = "Type your response..."
        
    # Collect user input
    prompt = st.chat_input(
        placeholder=placeholder, 
        disabled=is_flow_complete # Only disable if the structured flow is complete
    )
    
    if prompt:
        make_api_call(prompt)

if __name__ == "__main__":
    main_app()
