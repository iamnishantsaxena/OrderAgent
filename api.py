from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pipeline import OrderProcessor
from pydantic import BaseModel
from typing import Optional
import PyPDF2
import io

app = FastAPI(title="Order Intelligence API")
processor = OrderProcessor()

class OrderInput(BaseModel):
    text: str
    source_type: str = "text"

@app.post("/process-order")
async def process_order(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Process an order from text or file upload"""
    
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")
    
    # Handle file upload
    if file:
        content = await file.read()
        
        if file.filename.endswith('.pdf'):
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            source_type = "pdf"
        else:
            # Assume text file
            text = content.decode('utf-8')
            source_type = "email" if "From:" in text or "Subject:" in text else "text"
    else:
        source_type = "email" if "From:" in text or "Subject:" in text else "text"
    
    # Process through agent
    result = processor.process_order(text, source_type)
    
    return JSONResponse(content=result)

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "Order Intelligence Agent"}

# Run with: uvicorn api:app --reload