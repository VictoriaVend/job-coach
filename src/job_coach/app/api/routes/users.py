from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
def register_user():
    return {"msg": "user created"}


@router.post("/login")
def login_user():
    return {"msg": "user logged in"}
