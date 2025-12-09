# Pydantic models for request/response validation
from pydantic import BaseModel
from typing import List, Optional

class MessageParam(BaseModel):
    """
    Schema for a single message in the API request.
    """
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    Schema for the chat completion request.
    """
    model: str
    messages: List[MessageParam]
    # Optional session_id to continue a specific conversation
    session_id: Optional[str] = None