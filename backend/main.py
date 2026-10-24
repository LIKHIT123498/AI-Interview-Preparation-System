import os
from fastapi import FastAPI,UploadFile,File,Form,Depends,HTTPException,WebSocket,WebSocketDisconnect
from sqlalchemy.orm import Session
from database import get_db,engine,Base,ensure_interview_session_columns
from service.parser import extract_text_from_pdf
from service.gemini_ai import analyze_resume_vs_jd
from models_db import InterviewSession,InterviewTurn
from service.interview_agent import start_interview_chat
from fastapi.middleware.cors import CORSMiddleware
# Create database tables automatically on startup (for development)
Base.metadata.create_all(bind=engine)
ensure_interview_session_columns()

app=FastAPI(title="AI Interview Prep API",version="1.0")
# --- ADD THIS CORS CONFIGURATION ---
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allows your Vite React frontend and configured production origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers (including multipart/form-data)
)
# ----------------------------------
@app.post("/api/v1/analyze-resume")
async def analyze_resume_endpoint(
   user_id:int=Form(...),
   job_description:str=Form(...),
   file:UploadFile=File(...),
   db:Session=Depends(get_db)  
):
    """
    Accepts a PDF resume, parses text, and uses Gemini to cross-examine
    the resume against the target Job Description.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400,detail="Only PDF files are supported.")
    file_bytes = await file.read()

    resume_text=extract_text_from_pdf(file_bytes)

    if not resume_text.strip():
        raise HTTPException(status_code=400,detail="Could not extract text from provided PDF.")
    try:
        analysis_result = analyze_resume_vs_jd(resume_text, job_description)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Gemini AI capacity issue: {str(e)}")

    if isinstance(analysis_result, dict) and "error" in analysis_result and "readiness_score" not in analysis_result:
        raise HTTPException(status_code=503, detail=analysis_result.get("error", "AI service capacity issue."))

    new_session=InterviewSession(
        user_id=user_id,
        job_description=job_description,
        resume_text=resume_text,
        status="in_progress",
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return{
        "status":"success",
        "filename":file.filename,
        "session_id":new_session.id,
        "analysis":analysis_result
    }

@app.get("/")
def health_check():
    return {"status":"AI Interview Prep Backend is running smoothly with FastAPI and Gemini"}

@app.websocket("/ws/interview/{session_id}")
async def websocket_interview_endpoint(websocket: WebSocket, session_id:int,db: Session=Depends(get_db)):
    await websocket.accept()

    #1. Fetch session details from DB
    session_record=db.query(InterviewSession).filter(InterviewSession.id==session_id).first()
    if not session_record:
        await websocket.send_json({"error":"Session not found."})
        await websocket.close()
        return

    #2. Initialize the Gemini Agent
    chat_session=start_interview_chat(
        candidate_context=session_record.resume_text or "No resume provided.",
        job_description=session_record.job_description or "General software engineering role.",
    )

    turn_counter=1

    # Start the interview with an opening question
    try:
        opening_response=chat_session.send_message(
            "Hello, I am ready to begin the interview. Please ask your first question based on my resume.")
        await websocket.send_json(
            {
                "turn":turn_counter,
                "speaker":"AI",
                "message":opening_response.text
            })

        #3. Enter the active Interview Loop
        while True:
            # Wait for candidate's answer via WebSocket
            data=await websocket.receive_text()

            #Send candidate's answer to Gemini
            ai_response=chat_session.send_message(data)

            # Save the Turn to the Database
            new_turn=InterviewTurn(
                session_id=session_id,
                turn_index=turn_counter,
                user_answer=data,
                ai_question=ai_response.text,
                drill_down_triggered=False # Can be dynamically set based on prompt evaluations later
            )
            db.add(new_turn)
            db.commit()

            turn_counter+=1

            #Send the AI's follow-up question Can be dynamically set based on prompt evaluations later
            await websocket.send_json({
                "turn":turn_counter,
                "speaker":"AI",
                "message":ai_response.text
            })
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")
        session_record.status="completed"
        db.commit()
