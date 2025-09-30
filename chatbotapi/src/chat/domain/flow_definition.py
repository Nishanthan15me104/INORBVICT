# --- Domain Layer: Core Data Structures and Validation (with Pydantic) ---
from pydantic import BaseModel, field_validator, ValidationError
from typing import Optional

# Define the model that represents the final collected project data
class ProjectData(BaseModel):
    """Pydantic model for project intake data validation."""
    name: str
    projectType: str
    duration: int
    budget: int

    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Name must be at least 3 characters long.")
        return v
    
    @field_validator('projectType', mode='before')
    @classmethod
    def validate_project_type(cls, v):
        if not v or len(v.split()) < 2:
            raise ValueError("Project type must be described in at least two words.")
        return v

    @field_validator('duration', mode='before')
    @classmethod
    def validate_duration(cls, v):
        try:
            num = int(v)
            if num <= 0:
                raise ValueError("Duration must be a positive number of weeks.")
            return num
        except ValueError:
            raise ValueError("Duration must be a valid integer.")

    @field_validator('budget', mode='before')
    @classmethod
    def validate_budget(cls, v):
        try:
            num = int(v)
            if num <= 100:
                raise ValueError("Budget must be greater than $100.")
            return num
        except ValueError:
            raise ValueError("Budget must be a valid integer.")

# The conversation flow definition, now referencing the ProjectData keys
CHAT_FLOW = [
    { 
        'key': 'name', 
        'prompt': "Welcome! To start, what is your **full name**?",
        'placeholder': "e.g., Alex Johnson",
        'model_field': 'name',
    },
    { 
        'key': 'projectType', 
        'prompt': "What **type of project** are you planning?",
        'placeholder': "e.g., Web App, Data Analysis, Chatbot",
        'model_field': 'projectType',
    },
    { 
        'key': 'duration', 
        'prompt': "Approximately how many **weeks** will the project take?",
        'placeholder': "e.g., 8",
        'type': 'number',
        'model_field': 'duration',
    },
    { 
        'key': 'budget', 
        'prompt': "What is the approximate **budget** for this project (in USD)?",
        'placeholder': "e.g., 10000",
        'type': 'number',
        'model_field': 'budget',
    },
]
