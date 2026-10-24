import os
import json
import time
from google import genai
from google.genai.errors import ServerError
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_resume_vs_jd(resume_text: str, jd_text: str) -> dict:
    """
    Sends resume text and job description to Gemini to extract insights,
    gaps, and custom interview angles.
    
    Includes automatic retries with exponential backoff on 503 / ServerError spikes,
    with fallback to alternate model variants (gemini-3.8-flash).
    """
    prompt = f"""
    You are an expert technical recruiter and hiring manager. 
    Analyze the following candidate Resume against the provided Job Description (JD).

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
    - "suggested_focus_areas": List of specific project talking points or potential weak spots to drill down on during a mock interview.
    - "readiness_score": An integer score from 1 to 100 estimating how well the candidate matches the JD.
    
    Return ONLY valid JSON.
    """

    models_to_try = ['gemini-2.5-flash', 'gemini-3.8-flash']
    max_retries = 3
    base_delay = 2
    last_server_error = None

    for model_name in models_to_try:
        delay = base_delay
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:-3].strip()
                    
                return json.loads(raw_text)

            except ServerError as e:
                last_server_error = e
                print(f"[Gemini] ServerError (503/server capacity) on {model_name}, attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"[Gemini] Retries exhausted for {model_name}. Attempting fallback model...")
                    break
            except Exception as e:
                return {
                    "error": "Failed to parse response or communicate with Gemini",
                    "exception": str(e)
                }

    if last_server_error:
        raise last_server_error

    return {
        "error": "Failed to parse response or communicate with Gemini",
        "exception": "Capacity error across all retries and fallback models"
    }