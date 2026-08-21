from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import shutil

from ..database import get_db
from .auth import get_current_farmer
from ..chatbot.rag_engine import rag_engine
from ..chatbot.response_generator import response_generator
from ..chatbot.voice_processor import voice_processor
from ..chatbot.tts_engine import tts_engine

router = APIRouter(prefix="/chatbot", tags=["AI Farming Consultant Agent"])

# Create temporary upload directory for voice recordings
TEMP_VOICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "temp_voice"))

class ChatRequest(BaseModel):
    message: str
    gemini_key: Optional[str] = None
    tts_preference: Optional[str] = "AUTO"

class ChatResponse(BaseModel):
    # New expanded response fields
    answer: str
    detected_language: str
    normalized_query: str
    intent: str
    confidence: float
    sources: List[str]
    retrieval_score: float
    crop_entity: Optional[str] = None
    tts_config: dict
    
    # Backward compatibility fields (mapping to old React frontend usage)
    response: str
    source: str
    matched_topic: str

@router.post("/chat", response_model=ChatResponse)
def consult_agricultural_advisor(
    request: ChatRequest,
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # 1. Process query in RAG pipeline
    rag_result = rag_engine.process_query(
        query=request.message,
        db=db,
        farmer=current_farmer,
        api_key=request.gemini_key
    )
    
    # 2. Generate natural language response
    answer = response_generator.generate_response(
        rag_data=rag_result,
        api_key=request.gemini_key
    )
    
    # Save the dialogue exchange in the session memory
    rag_engine.save_session_response(
        farmer_id=current_farmer.id if current_farmer else 0,
        user_query=request.message,
        bot_response=answer
    )
    
    # 3. Generate Speech configuration
    tts_config = tts_engine.get_speech_config(
        text=answer,
        detected_language=rag_result["detected_language"],
        preference=request.tts_preference or "AUTO"
    )
    
    # 4. Construct response
    first_source = rag_result["sources"][0] if rag_result["sources"] else "Kerala Agricultural University"
    
    return ChatResponse(
        answer=answer,
        detected_language=rag_result["detected_language"],
        normalized_query=rag_result["normalized_query"],
        intent=rag_result["intent"],
        confidence=rag_result["intent_confidence"],
        sources=rag_result["sources"],
        retrieval_score=rag_result["retrieval_score"],
        crop_entity=rag_result["crop_entity"],
        tts_config=tts_config,
        # Map to original fields to prevent breaking the frontend
        response=answer,
        source=first_source,
        matched_topic=rag_result["intent"]
    )

@router.post("/voice", response_model=ChatResponse)
def consult_advisor_via_voice(
    file: UploadFile = File(...),
    gemini_key: Optional[str] = Form(None),
    tts_preference: Optional[str] = Form("AUTO"),
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Ensure temporary upload directory exists
    os.makedirs(TEMP_VOICE_DIR, exist_ok=True)
    
    # Save the file with a unique name
    file_extension = os.path.splitext(file.filename)[1] or ".wav"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(TEMP_VOICE_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded audio file: {e}"
        )
        
    # Process voice file to transcribe
    try:
        transcription_res = voice_processor.transcribe_audio(file_path)
        transcript = transcription_res["transcript"]
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {e}"
        )
    finally:
        # Clean up temporary voice file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    # Run the RAG and LLM pipeline on the transcribed text
    rag_result = rag_engine.process_query(
        query=transcript,
        db=db,
        farmer=current_farmer,
        api_key=gemini_key
    )
    
    answer = response_generator.generate_response(
        rag_data=rag_result,
        api_key=gemini_key
    )
    
    # Save the dialogue exchange in the session memory
    rag_engine.save_session_response(
        farmer_id=current_farmer.id if current_farmer else 0,
        user_query=transcript,
        bot_response=answer
    )
    
    tts_config = tts_engine.get_speech_config(
        text=answer,
        detected_language=rag_result["detected_language"],
        preference=tts_preference or "AUTO"
    )
    
    first_source = rag_result["sources"][0] if rag_result["sources"] else "Kerala Agricultural University"
    
    return ChatResponse(
        answer=answer,
        detected_language=rag_result["detected_language"],
        normalized_query=rag_result["normalized_query"],
        intent=rag_result["intent"],
        confidence=rag_result["intent_confidence"],
        sources=rag_result["sources"],
        retrieval_score=rag_result["retrieval_score"],
        crop_entity=rag_result["crop_entity"],
        tts_config=tts_config,
        # Map to original fields for frontend compatibility
        response=answer,
        source=first_source,
        matched_topic=rag_result["intent"]
    )
