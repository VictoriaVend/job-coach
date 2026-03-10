from fastapi import APIRouter, Depends
from pydantic import BaseModel

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.models.user import User

router = APIRouter(tags=["analysis"])


class SkillGapRequest(BaseModel):
    resume_text: str
    job_description: str


class SkillGapResponse(BaseModel):
    resume_skills: list[str]
    required_skills: list[str]
    matching_skills: list[str]
    missing_skills: list[str]
    match_score: float


@router.post("/skill-gap", response_model=SkillGapResponse)
def skill_gap(
    body: SkillGapRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze the skill gap between a resume and a job description."""
    try:
        from job_coach.ml.analysis import analyze_skill_gap

        result = analyze_skill_gap(
            resume_text=body.resume_text,
            job_description=body.job_description,
        )
        return SkillGapResponse(
            resume_skills=result.resume_skills,
            required_skills=result.required_skills,
            matching_skills=result.matching_skills,
            missing_skills=result.missing_skills,
            match_score=result.match_score,
        )
    except ImportError:
        return SkillGapResponse(
            resume_skills=[],
            required_skills=[],
            matching_skills=[],
            missing_skills=[],
            match_score=0.0,
        )
