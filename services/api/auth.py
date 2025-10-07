from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets, os

security = HTTPBasic()

USER = os.getenv("BASIC_USER", "demo")
PASS = os.getenv("BASIC_PASS", "demo123")

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct = secrets.compare_digest(credentials.username, USER) and \
              secrets.compare_digest(credentials.password, PASS)
    if not correct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return credentials.username
