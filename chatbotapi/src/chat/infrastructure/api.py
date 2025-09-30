# --- Infrastructure Layer: API Services (FastAPI Backend) ---
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, create_model # Import create_model
import uvicorn
from typing import Optional # Import Optional

# IMPORTANT: Import ProjectData model for validation
from chatbotapi.src.chat.domain.flow_definition import CHAT_FLOW, ProjectData 

app = FastAPI(title="Chatbot API")

# --- Request/Response Models ---
class FlowSubmitRequest(BaseModel):
    session_id: str
    user_input: str

class FlowResponse(BaseModel):
    status: str
    bot_message: str
    is_complete: bool
    data: dict

# In-memory dictionary for session state
API_SESSIONS = {}

def get_session(session_id: str):
    """Retrieves or initializes session state for a given ID."""
    if session_id not in API_SESSIONS:
        API_SESSIONS[session_id] = {
            'step_index': 0,
            'answers': {},
            'history': [],
            'is_complete': False,
        }
    return API_SESSIONS[session_id]

# --- API Endpoint: Submit ---
@app.post("/flow/submit", response_model=FlowResponse)
async def submit_flow_step(request: FlowSubmitRequest):
    """Handles the user's input and progresses the flow, applying Pydantic validation."""
    session_id = request.session_id
    user_input = request.user_input
    flow_state = get_session(session_id)
    
    if flow_state['is_complete']:
        return FlowResponse(
            status="complete",
            bot_message="Flow is already complete. Use /flow/reset to start over.",
            is_complete=True,
            data=flow_state['answers']
        )
        
    current_step_index = flow_state['step_index']

    # --- Core Flow Logic ---
    if current_step_index < len(CHAT_FLOW):
        current_step = CHAT_FLOW[current_step_index]
        current_key = current_step['key']
        
        # 1. Validation (Skip for initial empty call)
        if user_input:
            
            # CRITICAL FIX: Dynamically create a temporary model where all fields are optional
            # except the current one being validated. This prevents Pydantic from complaining
            # about missing required fields.
            temp_fields = {field: (Optional[ProjectData.model_fields[field].annotation], None) 
                           for field in ProjectData.model_fields}
            
            # The field being validated must use its actual type (or be marked optional if that's the final type)
            temp_fields[current_key] = (ProjectData.model_fields[current_key].annotation, ...) 
            
            # Create the temporary model based on the ProjectData configuration
            TempValidator = create_model('TempValidator', __base__=ProjectData, **temp_fields)

            try:
                # Use the temporary model to validate only the current input
                TempValidator(**{current_key: user_input})
                
                # If validation passes, now we can safely store the data
                flow_state['answers'][current_key] = user_input
                flow_state['history'].append({"role": "user", "content": user_input})
                
                # Advance step (only on successful validation)
                flow_state['step_index'] += 1

            except ValidationError as e:
                # Extract the specific error message for the current field
                # This should now only find errors related to the current field
                error_msg = next((err['msg'] for err in e.errors() if err['loc'][0] == current_key), "Invalid input.")
                
                # Return an error response, but do NOT advance the step.
                return FlowResponse(
                    status="validation_error",
                    bot_message=f"Input Error: {error_msg} Please try again.",
                    is_complete=False,
                    data=flow_state['answers']
                )

    # --- Determine Next Message/Completion ---
    if flow_state['step_index'] < len(CHAT_FLOW):
        next_step = CHAT_FLOW[flow_state['step_index']]
        # Use the name of the user if available for a personalized touch
        name = flow_state['answers'].get('name', 'there') 
        bot_message = next_step['prompt'].replace("[name]", name)
        
        flow_state['history'].append({"role": "assistant", "content": bot_message, "key": next_step['key']})
        is_complete = False
    else:
        bot_message = "Thank you! The flow is now complete."
        flow_state['is_complete'] = True
        is_complete = True
    
    return FlowResponse(
        status="success",
        bot_message=bot_message,
        is_complete=is_complete,
        data=flow_state['answers']
    )

# --- API Endpoint: Reset ---
@app.post("/flow/reset", response_model=FlowResponse)
async def reset_flow(session_id: str):
    """Resets the flow state for a given session ID."""
    if session_id in API_SESSIONS:
        del API_SESSIONS[session_id]
        
    return FlowResponse(
        status="success",
        bot_message="Flow state reset. Please start your conversation.",
        is_complete=False,
        data={}
    )

# --- Execution ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
