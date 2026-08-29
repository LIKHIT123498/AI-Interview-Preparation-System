import fitz

def extract_text_from_pdf(file_bytes: bytes)->str:
    """Extracts text content from uploaded PDF bytes."""
    doc=fitz.open(stream=file_bytes,filetype="pdf")
    text=""
    for page in doc:
        text+=page.get_text()
    return text
