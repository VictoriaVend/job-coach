from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def create_job():
    return {"msg": "job added"}
