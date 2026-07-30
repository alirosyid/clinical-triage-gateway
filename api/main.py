from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import logging

# Configure minimal logging for enterprise observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pii-gateway")

app = FastAPI(title="Zero-Trust Clinical Triage Gateway")

class PatientMessage(BaseModel):
    request_id: str
    raw_message: str

class TriageResponse(BaseModel):
    request_id: str
    redacted_message: str
    routing_bucket: str
    requires_hitl: bool

def redact_pii(text: str) -> str:
    """Masks sensitive numerical data (Phone numbers, NIK/ID cards) to ensure zero-trust compliance."""
    # Mask typical Indonesian phone numbers / NIK
    redacted = re.sub(r'\b(08|628|\+628)\d{7,11}\b', '[REDACTED_PHONE]', text)
    redacted = re.sub(r'\b\d{16}\b', '[REDACTED_NIK]', redacted)
    return redacted

def classify_intent(text: str) -> str:
    """Deterministic routing fallback before LLM processing."""
    text_lower = text.lower()
    
    # Specific Clinical Procedures
    if any(keyword in text_lower for keyword in ["occlusal", "adjustment", "rahang", "gigitan"]):
        return "clinical_occlusal_adjustment"
        
    # Academic / Residency Mapping
    if any(keyword in text_lower for keyword in ["koas", "stase", "resident", "semester 4"]):
        return "academic_resident_allocation"
        
    return "general_consultation"

@app.post("/api/v1/triage", response_model=TriageResponse)
async def process_triage(payload: PatientMessage):
    try:
        logger.info(f"Processing payload ID: {payload.request_id}")
        
        # Step 1: Zero-Trust Redaction
        safe_message = redact_pii(payload.raw_message)
        
        # Step 2: Preliminary State Routing
        bucket = classify_intent(safe_message)
        
        # Step 3: Human-In-The-Loop Flagging (Flag if message is too short/ambiguous)
        hitl_flag = len(safe_message.split()) < 4

        return TriageResponse(
            request_id=payload.request_id,
            redacted_message=safe_message,
            routing_bucket=bucket,
            requires_hitl=hitl_flag
        )

    except Exception as e:
        logger.error(f"Gateway Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Gateway Error")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "pii_redaction_gateway"}
