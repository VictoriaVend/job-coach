from fastapi import APIRouter

router = APIRouter()


@router.post("/query")
def upload_query():
    return {"msg": "query processed"}
