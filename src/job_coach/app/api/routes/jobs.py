from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def create_job():
    return {"msg": "job added"}


@router.get("/")
def get_job():
    return {"msg": "the job"}
