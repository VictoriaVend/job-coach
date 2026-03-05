from fastapi import APIRouter

router = APIRouter()


@router.post("/skill-gap")
def skill_gap():
    return {"msg": "skill gap analysis done"}
