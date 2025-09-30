# --- Application Layer: Flow Management and Business Logic ---
import streamlit as st
import time
from pydantic import ValidationError

# IMPORTANT: Corrected import path for the new structure
from chatbotapi.src.chat.domain.flow_definition import CHAT_FLOW, ProjectData 

# --- State Initialization and Management ---

def initialize_session_state():
    """Initializes or resets Streamlit session state variables."""
    if 'mode' not in st.session_state:
        # Default mode for initial setup is 'flow'
        st.session_state.mode = 'flow' 
        
    if 'flow_state' not in st.session_state:
        st.session_state.flow_state = {
            'step_index': 0,
            # Answers are stored here, which will be validated against ProjectData
            'answers': {}, 
            'history': [],
            'is_complete': False,
        }

def reset_flow_state():
    """Resets the state to restart the flow."""
    st.session_state.flow_state = {
        'step_index': 0,
        'answers': {},
        'history': [],
        'is_complete': False,
    }
    st.experimental_rerun() 

# --- UI Rendering Helpers (using Streamlit components) ---

def display_flow_history():
    """Renders all messages from the flow history state."""
    flow_state = st.session_state.flow_state
    
    if flow_state['is_complete']:
        st.sidebar.success("Flow Complete!")
    else:
        current_step = flow_state['step_index'] + 1
        total_steps = len(CHAT_FLOW)
        st.sidebar.info(f"Step {current_step} of {total_steps}")
        st.sidebar.subheader("Flow Mode Active")

    for message in flow_state['history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def display_flow_summary():
    """Renders the final project summary card."""
    answers = st.session_state.flow_state['answers']
    st.success("🎉 Flow Complete! Summary Generated 🎉")
    st.subheader("Project Intake Summary")
    
    col1, col2 = st.columns(2)
    
    def format_currency(value):
        try:
            # Format value if it is successfully parsed as an integer
            return f"${int(value):,}"
        except:
            return f"${value}" 
            
    # Attempt to validate the final data structure one last time before display
    try:
        ProjectData(**answers)
        st.info("✅ Final data validated successfully by Pydantic.")
    except ValidationError as e:
        # Display validation errors if any fields failed the final check
        error_details = "\n".join([f"- **{err['loc'][0]}**: {err['msg']}" for err in e.errors()])
        st.error(f"⚠️ Validation Errors Found:\n\n{error_details}")
        
    summary_data = [
        ("Client Name", answers.get('name'), col1),
        ("Project Type", answers.get('projectType'), col2),
        ("Estimated Duration", f"{answers.get('duration')} weeks", col1),
        ("Approximate Budget", format_currency(answers.get('budget')), col2),
    ]

    for label, value, col in summary_data:
        with col:
            st.metric(label=label, value=value)
            
    st.button("Start New Flow", on_click=reset_flow_state, use_container_width=True)


# --- Submission Logic ---

def handle_flow_submit(user_input):
    """Handles user input validation and state advancement using Pydantic."""
    flow_state = st.session_state.flow_state

    if flow_state['is_complete']:
        return 

    current_step = CHAT_FLOW[flow_state['step_index']]
    
    # 1. Validate the input using Pydantic's field validators
    try:
        # We use a temporary dictionary for Pydantic to validate the single field's input.
        ProjectData(**{current_step['model_field']: user_input})
        
    except ValidationError as e:
        # Extract the specific error message for the current field
        error_msg = next((err['msg'] for err in e.errors() if err['loc'][0] == current_step['model_field']), "Invalid input.")
        st.error(f"Validation Error: {error_msg}")
        return
        
    # 2. Store user answer in history and answers
    flow_state['history'].append({"role": "user", "content": user_input})
    flow_state['answers'][current_step['key']] = user_input
    
    # 3. Advance to next step
    flow_state['step_index'] += 1
    
    # 4. Check for completion and re-run 
    if flow_state['step_index'] >= len(CHAT_FLOW):
        flow_state['is_complete'] = True
    
    st.experimental_rerun()

def get_current_bot_response():
    """Determines and generates the next bot message if needed."""
    flow_state = st.session_state.flow_state
    if flow_state['is_complete']:
        return None, None

    current_step = CHAT_FLOW[flow_state['step_index']]
    
    # Check if the bot prompt needs to be displayed (only once per step)
    if not flow_state['history'] or flow_state['history'][-1].get('key') != current_step['key']:
        with st.chat_message("assistant"):
            with st.spinner('Thinking...'):
                time.sleep(0.5) 
            st.markdown(current_step['prompt'])
            
            # Store the bot message in history
            flow_state['history'].append({
                "role": "assistant", 
                "content": current_step['prompt'],
                "key": current_step['key'] 
            })
            
    return current_step['placeholder'], flow_state['is_complete']
