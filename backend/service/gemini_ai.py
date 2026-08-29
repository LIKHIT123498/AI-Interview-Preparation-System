import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_resume_vs_jd(resume_text:str,jd_text:str)->dict:
    """
    Sends resume text and job description to Gemini 2.5 Flash to extract insights,
    gaps, and custom interview angles. 
    """
    prompt=f"""
     You are an expert technical recruiter and hiring manager.
     Analyze the following candidate Resume against the provided Job Description(JD).

     ---
     RESUME TEXT:
     {resume_text}
     ---
     JOB DESCRIPTION:
     {jd_text}
     ---

     Provide a structured analysis in valid JSON format with the following keys:
     - "extracted_skills": List of relevant technical skills found in the resume.
     - "identified_gaps": List of missing skills, technologies, or experience gaps relative to the JD.
     - "suggested_focus_areas": List of specific project talking points or potential    
     - "readiness_score": An integer score from 1 to 100 estimating how well the candidate match the JD.
     
     Return ONLY valid JSON. No markdown ticks around it if possible, or standard parseable JSON.
     """

    response=client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )

    try:
        #Clean up code blocks if model outputs them
        raw_text=response.text.strip()
        if raw_text.startswith("```json"):
            raw_text=raw_text[7:-3].strip()
        elif raw_text.startswith("```"):
            raw_text=raw_text[3:-3].strip()

        return json.loads(raw_text)
    except Exception as e:
        # fallback if Json parsing fails
        return {
            "error":"Failed to pare JSON response from Gemini",
            "raw_output":response.text,
            "exception": str(e)
        }