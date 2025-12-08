import os
import requests
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal, DbSession, DbMessage

from datetime import datetime, timedelta  # Added for time calculation
from apscheduler.schedulers.background import BackgroundScheduler # Added for scheduling tasks

app = FastAPI()

# --- Pydantic Models (Input Validation) ---

class MessageParam(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[MessageParam]
    # Optional session_id to continue a conversation
    session_id: Optional[str] = None 

# --- Dependency: Database Session Management ---
def get_db():
    """
    Creates a new database session for each request and closes it afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# --- Background Task: Auto-Cleanup Logic ---
def cleanup_old_sessions():
    """
    Background task to delete sessions older than 7 days.
    
    Logic:
    1. Calculate the expiration date (current time - 7 days).
    2. Delete sessions created before this date.
    3. Due to 'cascade="all, delete"' in database.py, 
       messages associated with these sessions are automatically deleted.
    """
    print("[Auto-Cleanup] Starting cleanup task...")
    db = SessionLocal()
    try:
        # Define retention period: 7 days
        expiration_date = datetime.utcnow() - timedelta(days=7)
        
        # Query and delete expired sessions
        deleted_count = db.query(DbSession).filter(DbSession.created_at < expiration_date).delete()
        db.commit()
        
        if deleted_count > 0:
            print(f"[Auto-Cleanup] Successfully deleted {deleted_count} expired sessions.")
        else:
            print("[Auto-Cleanup] No expired sessions found.")
            
    except Exception as e:
        print(f"[Auto-Cleanup] Error occurred during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

# --- Scheduler Initialization ---

# Initialize the background scheduler
scheduler = BackgroundScheduler()

# Schedule the cleanup job to run once every 24 hours (interval)
# You can change 'days=1' to 'minutes=1' for testing purposes
scheduler.add_job(cleanup_old_sessions, 'interval', days=1)

# Start the scheduler
scheduler.start()

# Ensure the scheduler shuts down when the app exits
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()



# --- API Endpoints ---
@app.post("/llm_api/chat/completions")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    
    # 1. Determine Session ID (Context Management)
    session_id = request.session_id
    db_session = None

    if session_id:
        # Try to retrieve existing session
        db_session = db.query(DbSession).filter(DbSession.session_id == session_id).first()
    
    if not db_session:
        # If no ID provided or session not found, create a new one
        db_session = DbSession(title="New Conversation")
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        session_id = str(db_session.session_id)

    # 2. Save User's New Message (Short-term Memory Write)
    # Assume the last message in the list is the new user input
    last_user_msg = request.messages[-1]
    
    if last_user_msg.role == 'user':
        user_db_msg = DbMessage(
            session_id=session_id,
            role="user",
            content=last_user_msg.content
        )
        db.add(user_db_msg)
        db.commit()

    # 3. Retrieve Context (Memory Retrieval)
    # Fetch the last 20 messages from this session to provide context
    history = db.query(DbMessage).filter(DbMessage.session_id == session_id)\
                .order_by(DbMessage.created_at.asc())\
                .limit(20).all()
    
    # Format history for vLLM
    context_messages = [{"role": msg.role, "content": msg.content} for msg in history]

    # 4. Call vLLM Backend (Inference)
    gpu_ip = os.getenv("GPU_SERVER_IP")
    api_key = os.getenv("LLM_API_KEY")
    
    # Use the internal port 8000 of the GPU server
    # Ensure strict error handling
    if not gpu_ip:
        raise HTTPException(status_code=500, detail="GPU_SERVER_IP not configured")

    vllm_url = f"http://{gpu_ip}:8000/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": request.model,
        "messages": context_messages # Pass the full context with memory
    }

    try:
        # Forward request to vLLM
        response = requests.post(vllm_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        ai_data = response.json()
        
        # Extract AI content
        ai_content = ai_data['choices'][0]['message']['content']
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"vLLM Connection Error: {str(e)}")

    # 5. Save AI's Response (Short-term Memory Write)
    ai_db_msg = DbMessage(
        session_id=session_id,
        role="assistant",
        content=ai_content
    )
    db.add(ai_db_msg)
    db.commit()

    # 6. Return Response with Session ID
    # Attach session_id so the frontend knows which session to continue
    ai_data['session_id'] = session_id
    return ai_data



# --- Additional Endpoints for Session Management ---
@app.get("/llm_api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DbSession).all()
    return sessions

@app.get("/llm_api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(DbMessage)\
                 .filter(DbMessage.session_id == session_id)\
                 .order_by(DbMessage.created_at.asc())\
                 .all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    return messages