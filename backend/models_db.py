from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base  # or app.database depending on your imports

class InterviewSession(Base):
    __tablename__ = "interview_sessions"  # <--- Make sure this line is present and correct

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_description = Column(Text)
    status = Column(String(50), default="in_progress")
    started_at = Column(TIMESTAMP, server_default=func.now())

    turns = relationship("InterviewTurn", back_populates="session")

class InterviewTurn(Base):
    __tablename__ = "interview_turns"   # <--- Make sure this line is present here too

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"))
    turn_index = Column(Integer)
    user_answer = Column(Text)
    ai_question = Column(Text)
    drill_down_triggered = Column(Boolean, default=False)
    
    session = relationship("InterviewSession", back_populates="turns")