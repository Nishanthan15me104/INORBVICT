# --- Infrastructure Layer: API Services (FastAPI Backend) ---
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, create_model
import uvicorn
from typing import Optional 
import os 
from dotenv import load_dotenv 

# IMPORTANT: Import ProjectData model for validation
from chatbotapi.src.chat.domain.flow_definition import CHAT_FLOW, ProjectData 

# Import the RAG/LLM generator service
# Assuming the project structure allows this import from the API level
from chatbotapi.src.chat.application.convo.response_generation import HybridGenerator 

# --- Initialization of Hybrid Generator ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    # NOTE: In a real environment, you might want to handle this more gracefully, 
    # but for a quick setup, raising an error ensures the API doesn't start without the key.
    print("FATAL ERROR: GROQ_API_KEY environment variable not found. RAG functionality will fail.")
    # Attempt to initialize even with an empty key, the Groq client might handle it.
    # However, for robustness, we use a placeholder that will likely fail if not set, mirroring the test script's requirement.
    GROQ_API_KEY = GROQ_API_KEY or "DUMMY_KEY"

# Initialize the generator globally. This uses the logic from your Canvas file.
HYBRID_GENERATOR = HybridGenerator(groq_api_key=GROQ_API_KEY) 

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
    mode: str = "initial" # Added: To communicate the current operational mode back to the client

# In-memory dictionary for session state
API_SESSIONS = {}

def get_session(session_id: str):
    """Retrieves or initializes session state for a given ID."""
    if session_id not in API_SESSIONS:
        API_SESSIONS[session_id] = {
            'mode': 'initial', # Added: 'initial', 'flow', or 'rag'
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
    current_mode = flow_state['mode']
    
    # Message templates
    INITIAL_PROMPT = "Hello! I am a modular chatbot. Would you like to use the **Flow-based Project Planner** or the **Jordan Peterson RAG Chatbot**? (Respond with 'Flow' or 'RAG')."
    INVALID_MODE_MESSAGE = "I couldn't understand that. Please respond with 'Flow' to start the Project Planner or 'RAG' to start the Jordan Peterson Chatbot."

    # 0. Initial Mode Selection Logic
    if current_mode == 'initial':
        if not user_input:
            # First call, just return the prompt
            return FlowResponse(
                status="success",
                bot_message=INITIAL_PROMPT,
                is_complete=False,
                data={},
                mode='initial'
            )
        
        # User is responding to mode selection
        lower_input = user_input.lower().strip()
        
        if 'flow' in lower_input:
            flow_state['mode'] = 'flow'
            # Fall through to the Flow logic (to get the first question)
            current_mode = flow_state['mode']
            
        elif 'rag' in lower_input:
            flow_state['mode'] = 'rag'
            flow_state['history'].append({"role": "user", "content": user_input})
            return FlowResponse(
                status="success",
                bot_message="RAG Chatbot selected. Ask me any question about Jordan Peterson.",
                is_complete=False,
                data={},
                mode='rag'
            )
        else:
            # Invalid selection
            flow_state['history'].append({"role": "user", "content": user_input})
            return FlowResponse(
                status="validation_error",
                bot_message=INVALID_MODE_MESSAGE,
                is_complete=False,
                data={},
                mode='initial'
            )
            
    # 1. RAG Mode Logic
    if current_mode == 'rag':
        if not user_input:
            # Prevent the initial empty call from executing the generator
            return FlowResponse(
                status="success",
                bot_message="RAG Chatbot is active. Ask your question.",
                is_complete=False,
                data={},
                mode='rag'
            )
            
        # Use the HybridGenerator for the RAG query
        try:
            # Add user input to history for context/display if needed
            flow_state['history'].append({"role": "user", "content": user_input})
            
            # Run the hybrid logic (which classifies and generates)
            result = HYBRID_GENERATOR(user_input)
            
            # The bot response is the content of the result
            bot_message = result['response']
            
            flow_state['history'].append({"role": "assistant", "content": bot_message})
            
            return FlowResponse(
                status="success",
                bot_message=bot_message,
                is_complete=False, # RAG is continuous, never 'complete'
                data={},
                mode='rag'
            )
        except Exception as e:
            # This handles exceptions from the HybridGenerator chain (e.g., API errors)
            print(f"RAG Error: {e}")
            return FlowResponse(
                status="error",
                bot_message=f"An error occurred while processing the RAG query: {e}",
                is_complete=False,
                data={},
                mode='rag'
            )


    # 2. Flow Mode Logic (Existing code, now only executed if current_mode == 'flow')
    if current_mode == 'flow':
        
        if flow_state['is_complete']:
            return FlowResponse(
                status="complete",
                bot_message="Flow is already complete. Use /flow/reset to start over.",
                is_complete=True,
                data=flow_state['answers'],
                mode='flow'
            )
        
        current_step_index = flow_state['step_index']

        if current_step_index < len(CHAT_FLOW):
            current_step = CHAT_FLOW[current_step_index]
            current_key = current_step['key']
            
            # Validation (Skip for initial empty call or just after mode selection)
            if user_input:
                
                temp_fields = {field: (Optional[ProjectData.model_fields[field].annotation], None) 
                               for field in ProjectData.model_fields}
                
                temp_fields[current_key] = (ProjectData.model_fields[current_key].annotation, ...) 
                
                TempValidator = create_model('TempValidator', __base__=ProjectData, **temp_fields)

                try:
                    TempValidator(**{current_key: user_input})
                    
                    flow_state['answers'][current_key] = user_input
                    flow_state['history'].append({"role": "user", "content": user_input})
                    
                    flow_state['step_index'] += 1

                except ValidationError as e:
                    error_msg = next((err['msg'] for err in e.errors() if err['loc'][0] == current_key), "Invalid input.")
                    
                    return FlowResponse(
                        status="validation_error",
                        bot_message=f"Input Error: {error_msg} Please try again.",
                        is_complete=False,
                        data=flow_state['answers'],
                        mode='flow'
                    )

        # --- Determine Next Message/Completion ---
        if flow_state['step_index'] < len(CHAT_FLOW):
            next_step = CHAT_FLOW[flow_state['step_index']]
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
            data=flow_state['answers'],
            mode='flow'
        )
    
    # Fallback for unexpected state change
    return FlowResponse(
        status="error",
        bot_message="An unexpected state was reached. Please reset the flow.",
        is_complete=False,
        data={},
        mode='initial'
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
        data={},
        mode='initial'
    )

# --- Execution ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
