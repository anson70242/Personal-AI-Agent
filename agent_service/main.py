import os
import httpx
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

# Import local modules
from database import SessionLocal
import schemas
import crud
# import rag # Reserved for future use

# --- Configuration ---
GPU_SERVER_IP = os.getenv("GPU_SERVER_IP")
LLM_API_KEY = os.getenv("LLM_API_KEY")
VLLM_TIMEOUT = 60.0

# --- Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    Initializes the background scheduler for cleanup tasks.
    """
    scheduler = BackgroundScheduler()
    
    # Wrapper function to create a DB session for the scheduler
    def scheduled_cleanup():
        print("[Auto-Cleanup] Starting cleanup task...")
        with SessionLocal() as db:
            try:
                count = crud.cleanup_expired_sessions(db)
                if count > 0:
                    print(f"[Auto-Cleanup] Deleted {count} expired sessions.")
            except Exception as e:
                print(f"[Auto-Cleanup] Error: {e}")

    # Run cleanup daily
    scheduler.add_job(scheduled_cleanup, 'interval', days=1)
    scheduler.start()
    
    yield # Application runs here
    
    # Shutdown logic
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# --- Dependency ---
def get_db():
    """
    Creates a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/llm_api/chat/completions")
async def chat_endpoint(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    
    # 1. Manage Session (Get existing or create new)
    session_id = crud.get_or_create_session(db, request.session_id)

    # 2. Save User's Message to DB
    last_user_msg = request.messages[-1]
    if last_user_msg.role == 'user':
        crud.save_message(db, session_id, "user", last_user_msg.content)

    # 3. Retrieve Context (History)
    context_messages = crud.get_chat_history(db, session_id)
    
    # (Optional) Future RAG integration point:
    # docs = rag.retrieve_documents(last_user_msg.content)
    # context_messages.append({"role": "system", "content": f"Context: {docs}"})

    # 4. Call vLLM Backend (Non-blocking Async Call)
    if not GPU_SERVER_IP:
        raise HTTPException(status_code=500, detail="GPU_SERVER_IP not configured")

    vllm_url = f"http://{GPU_SERVER_IP}:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    # Construct payload for vLLM
    payload = {
        "model": request.model,
        "messages": context_messages
    }

    try:
        # Use httpx for asynchronous HTTP requests
        async with httpx.AsyncClient(timeout=VLLM_TIMEOUT) as client:
            response = await client.post(vllm_url, headers=headers, json=payload)
            response.raise_for_status() # Raise exception for 4xx/5xx errors
            ai_data = response.json()
            
        ai_content = ai_data['choices'][0]['message']['content']

    except httpx.HTTPStatusError as e:
         raise HTTPException(status_code=e.response.status_code, detail=f"vLLM Provider Error: {e.response.text}")
    except httpx.RequestError as e:
         raise HTTPException(status_code=500, detail=f"vLLM Connection Failed: {str(e)}")

    # 5. Save AI's Response to DB
    crud.save_message(db, session_id, "assistant", ai_content)

    # 6. Return Response with Session ID
    ai_data['session_id'] = session_id
    return ai_data

@app.get("/llm_api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    """
    Retrieve all available sessions.
    """
    from database import DbSession # Local import to avoid circular dependency if expanded
    return db.query(DbSession).all()

@app.get("/llm_api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieve all messages for a specific session.
    """
    # Re-use the logic from crud, or write a custom query if we need all messages (not just limit 20)
    # For this endpoint, we usually want the full history.
    from database import DbMessage
    messages = db.query(DbMessage)\
                 .filter(DbMessage.session_id == session_id)\
                 .order_by(DbMessage.created_at.asc())\
                 .all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    return messages