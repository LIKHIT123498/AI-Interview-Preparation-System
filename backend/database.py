import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL","mysql+pymysql://root:password@localhost:3306/ai_interview_db")

engine=create_engine(DATABASE_URL)

engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_interview_session_columns():
    columns = {column["name"] for column in inspect(engine).get_columns("interview_sessions")}
    if "resume_text" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE interview_sessions ADD COLUMN resume_text TEXT NULL")
            )
