# All database interactions are isolated here.
from sqlalchemy.orm import Session
from database import DbSession, DbMessage
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import desc

# Constants
HISTORY_LIMIT = 20

def get_or_create_session(db: Session, session_id: Optional[str]) -> str:
    """
    Retrieves an existing session ID or creates a new one if not found/provided.
    """
    if session_id:
        db_session = db.query(DbSession).filter(DbSession.session_id == session_id).first()
        if db_session:
            return str(db_session.session_id)
    
    # Create new session
    new_session = DbSession(title="New Conversation")
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return str(new_session.session_id)

def save_message(db: Session, session_id: str, role: str, content: str):
    """
    Saves a message (User or AI) to the database.
    """
    msg = DbMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()

def get_chat_history(db: Session, session_id: str) -> List[dict]:
    """
    Fetches the recent chat history for the LLM context.
    """
    # newest first
    history = db.query(DbMessage)\
                .filter(DbMessage.session_id == session_id)\
                .order_by(DbMessage.created_at.desc())\
                .limit(HISTORY_LIMIT).all()

    if not history:
        return []

    # return oldest first
    history.reverse()
    
    return [{"role": msg.role, "content": msg.content} for msg in history]

def cleanup_expired_sessions(db: Session, days: int = 7) -> int:
    """
    Deletes sessions older than the specified number of days.
    """
    expiration_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = db.query(DbSession).filter(DbSession.created_at < expiration_date).delete()
    db.commit()
    return deleted_count