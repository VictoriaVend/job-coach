from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from job_coach.app.api.dependencies import get_current_user
from job_coach.app.core.logger import logger
from job_coach.app.models.user import User

router = APIRouter(tags=["analysis"])


class SkillGapRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, max_length=50_000)
    job_description: str = Field(..., min_length=1, max_length=50_000)


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
    logger.info(f"User {current_user.id} requested skill gap analysis")
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
    except ImportError as e:
        logger.error(f"Skill gap analysis error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML dependencies are not installed. Run: pip install '.[ml]'",
        )


class SemanticMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, max_length=50_000)
    job_description: str = Field(..., min_length=1, max_length=50_000)


class SemanticMatchResponse(BaseModel):
    similarity_score: float
    interpretation: str


@router.post("/semantic-match", response_model=SemanticMatchResponse)
def semantic_job_match(
    body: SemanticMatchRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate the semantic vector similarity between a resume and a job description.

    Unlike skill gap analysis which extracts explicit keywords, this pipeline uses
    dense vector embeddings to understand the implicit contextual match.
    """
    logger.info(f"User {current_user.id} requested semantic match analysis")
    try:
        from job_coach.ml.analysis.semantic_match import generate_semantic_match

        result = generate_semantic_match(
            resume_text=body.resume_text,
            job_description=body.job_description,
        )
        return SemanticMatchResponse(
            similarity_score=result.similarity_score,
            interpretation=result.interpretation,
        )
    except ImportError as e:
        logger.error(f"Semantic match analysis error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML dependencies are not installed. Run: pip install '.[ml]'",
        )
