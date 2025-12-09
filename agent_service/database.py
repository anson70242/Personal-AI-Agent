# Setup connection and define ORM models.
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import os
import uuid
from datetime import datetime

# 1. Load database configurations from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "agent_memory")
POSTGRES_HOST = "db" # Service name in docker-compose

# Construct the connection string
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

# 2. Create the database engine
engine = create_engine(DATABASE_URL)

# 3. Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class for ORM models
Base = declarative_base()

# --- ORM Models Definition ---

class DbSession(Base):
    """
    Represents a conversation session (short-term memory block).
    """
    __tablename__ = "sessions"
    
    # Primary Key: UUID
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(Text, nullable=True)
    
    # Relationship: One Session has many Messages
    messages = relationship("DbMessage", back_populates="session", cascade="all, delete")

class DbMessage(Base):
    """
    Represents a single message within a session.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"))
    role = Column(String, nullable=False)   # 'user' or 'assistant'
    content = Column(Text, nullable=False)  # The actual text content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Link back to the parent Session
    session = relationship("DbSession", back_populates="messages")