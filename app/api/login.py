from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

fake_users_db = {"sad": {"username": "sad", "password": "123"}}

router = APIRouter()

api_key = os.environ.get("API_KEY")


def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(request: Request):
    token = request.cookies.get("access_token") or request.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token not found")
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # getting username
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token error: {str(e)}")


@router.post("/login/{key}/{login}/{password}")
async def login(
    key: str,
    login: str,
    password: str,
):
    if key != api_key:
        return JSONResponse({"error": "api key is invalid!"})

    user = fake_users_db.get(login)
    if not user or user["password"] != password:
        raise HTTPException(status_code=400, detail="Incorrect login or password")

    token = create_jwt_token({"sub": login})
    response = JSONResponse({"message": "success"})
    response.set_cookie(
        key="access_token", value=token, httponly=True, secure=True, samesite="lax"
    )
    return JSONResponse(
        {
            "access_token": token,
        }
    )


@router.get("/protected")
async def protected(username: str = Depends(verify_token)):
    return {"message": f"Hi, {username}! This is a protected zone!"}
