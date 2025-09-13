from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional

from ..services.job_manager import job_manager, VideoTranslationRequest
from ..models.translation_job import JobStatus


router = APIRouter()


class CreateTranslationRequest(BaseModel):
    youtube_url: HttpUrl
    source_language: str
    target_language: str

    @validator("source_language", "target_language")
    def _lang_code(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) != 2 or not v.isalpha():
            raise ValueError("language must be ISO 639-1 code (e.g., 'en', 'es')")
        return v


class CreateTranslationResponse(BaseModel):
    job_id: str
    stage: str
    progress: float


class JobStatusResponse(BaseModel):
    job_id: str
    stage: str
    progress: float
    error: Optional[str] = None


@router.post("/jobs", response_model=CreateTranslationResponse, status_code=status.HTTP_201_CREATED)
def create_job(req: CreateTranslationRequest):
    job_id = job_manager.create_job(
        request=VideoTranslationRequest(
            youtube_url=str(req.youtube_url),
            source_language=req.source_language,
            target_language=req.target_language,
        )
    )
    st = job_manager.get_job_status(job_id)
    if not st:
        raise HTTPException(status_code=500, detail="Failed to create job")
    return CreateTranslationResponse(job_id=st.job_id, stage=st.stage.value, progress=st.progress)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    st: Optional[JobStatus] = job_manager.get_job_status(job_id)
    if not st:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=st.job_id, stage=st.stage.value, progress=st.progress, error=st.error)
