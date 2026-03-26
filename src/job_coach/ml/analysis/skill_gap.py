"""Skill gap analysis: compare resume skills against job requirements."""

from __future__ import annotations

from dataclasses import dataclass

from job_coach.app.core.config import settings


@dataclass
class SkillGapResult:
    """Structured result from skill gap analysis."""

    resume_skills: list[str]
    required_skills: list[str]
    matching_skills: list[str]
    missing_skills: list[str]
    match_score: float


def extract_skills_via_llm(text: str, text_type: str = "resume") -> list[str]:
    """Use Ollama LLM to extract skills from text.

    Args:
        text: Resume text or job description.
        text_type: 'resume' or 'job_description'.

    Returns:
        List of extracted skill strings.
    """
    import httpx

    prompt = f"""Extract all technical and professional skills from the following
{text_type}. Return ONLY a JSON array of skill strings, nothing else.

Example output: ["Python", "FastAPI", "PostgreSQL", "Docker", "Machine Learning"]

Text:
{text[:3000]}

Skills (JSON array only):"""

    try:
        response = httpx.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        raw = response.json().get("response", "[]")

        # Parse the JSON array from LLM response
        import json

        # Try to find JSON array in response
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        return []

    except httpx.ConnectError:
        # Fallback: simple keyword extraction
        return _fallback_extract_skills(text)
    except Exception:
        return _fallback_extract_skills(text)


def _fallback_extract_skills(text: str) -> list[str]:
    """Simple keyword-based skill extraction fallback when LLM is unavailable."""
    known_skills = {
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "go",
        "rust",
        "sql",
        "nosql",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "terraform",
        "fastapi",
        "django",
        "flask",
        "react",
        "vue",
        "angular",
        "node.js",
        "git",
        "ci/cd",
        "linux",
        "rest",
        "graphql",
        "grpc",
        "machine learning",
        "deep learning",
        "nlp",
        "computer vision",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "pandas",
        "numpy",
        "data engineering",
        "etl",
        "spark",
        "airflow",
        "agile",
        "scrum",
        "jira",
        "confluence",
    }

    text_lower = text.lower()
    found = []
    for skill in known_skills:
        if skill in text_lower:
            found.append(skill.title() if len(skill) > 3 else skill.upper())
    return sorted(set(found))


def analyze_skill_gap(
    resume_text: str,
    job_description: str,
) -> SkillGapResult:
    """Run skill gap analysis between a resume and a job description.

    Flow:
    1. Extract skills from resume via LLM
    2. Extract required skills from job description via LLM
    3. Compute intersection, missing skills, and match score

    Args:
        resume_text: Full text of the resume.
        job_description: Full text of the job posting.

    Returns:
        SkillGapResult with skills analysis.
    """
    resume_skills = extract_skills_via_llm(resume_text, "resume")
    required_skills = extract_skills_via_llm(job_description, "job description")

    # Normalize for comparison
    resume_set = {s.lower().strip() for s in resume_skills}
    required_set = {s.lower().strip() for s in required_skills}

    matching = resume_set & required_set
    missing = required_set - resume_set

    match_score = len(matching) / len(required_set) * 100 if required_set else 0.0

    return SkillGapResult(
        resume_skills=sorted(resume_skills),
        required_skills=sorted(required_skills),
        matching_skills=sorted(s.title() for s in matching),
        missing_skills=sorted(s.title() for s in missing),
        match_score=round(match_score, 1),
    )
