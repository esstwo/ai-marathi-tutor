from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.services.tts import synthesize_marathi
from backend.dependencies.auth import get_current_parent

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str


@router.post("/speak")
def speak(req: TTSRequest, _parent_id: str = Depends(get_current_parent)):
    if not req.text or len(req.text) > 200:
        raise HTTPException(400, "Text must be 1-200 characters")
    audio_bytes = synthesize_marathi(req.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
