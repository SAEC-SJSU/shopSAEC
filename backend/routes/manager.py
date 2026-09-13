from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auth import check_manager_password

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
async def manager_login(body: LoginRequest):
    if not check_manager_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"ok": True}
