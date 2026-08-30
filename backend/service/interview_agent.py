import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def start_interview_chat(candidate_context: str,job_description: str):
    """
    Initializes a Gemini chat session with strict system instructions for the 'Grill Logic'. 
    """
    system_instruction=f"""
    You are a rigorous Senior Engineering Manager conducting a technical interview.
    You are evaluating a candidate based on this context:

    Candidate Context (Resume/Skills): {candidate_context}
    Target Job Description: {job_description}
    
    RULES:
    1. Do not be overly polite or use generic praise (e.g., avoid "Great answer!")
    2. Ask ONE focused question at a time. Do not read off a list.
    3. If the candidate uses buzzwords without depth (e.g., "I used FastAPI"), interrupt and drill down (e.g., "Why FastAPI over Spring Boot? How did you handle async database drivers?").
    4. keep your responses concise and conversational, as if speaking on a video call.
    5. Evaluate trade-offs, time/space complexity, and architecture choices.
    """

    #create a stateful chat session
    chat=client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
        )
    )
    return chat

