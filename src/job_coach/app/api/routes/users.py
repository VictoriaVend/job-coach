from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
def register_user():
    return {"msg": "user created"}
