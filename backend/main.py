from fastapi import FastAPI,UploadFile,File,Form,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db,engine,Base
from service.parser import extract_text_from_pdf
from service.gemini_ai import analyze_resume_vs_jd

# Create database tables automatically on startup (for development)
Base.metadata.create_all(bind=engine)

app=FastAPI(title="AI Interview Prep API",version="1.0")

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
    analysis_result=analyze_resume_vs_jd(resume_text,job_description)

    return{
        "status":"success",
        "filename":file.filename,
        "analysis":analysis_result
    }

@app.get("/")
def health_check():
    return {"status":"AI Interview Prep Backend is running smoothly with FastAPI and Gemini"}
