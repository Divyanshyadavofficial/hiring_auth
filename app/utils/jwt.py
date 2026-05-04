from datetime import datetime,timedelta
from jose import JWTError,jwt
from app.models_db.user import BlacklistToken
from sqlalchemy import select
import uuid
from app.core.config import settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict):
    to_encode = {}

    to_encode["user_id"] =data["user_id"]
    to_encode["role"] = data["role"]
    to_encode["jti"] = str(uuid.uuid4())

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp":expire,"type":"access"})

    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str,db):
    try: 
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)

        if payload.get("type")!="access":
            return None
        
        jti = payload.get("jti")
        if jti is None:
            return None
        
        result = await db.execute(
            select(BlacklistToken).where(BlacklistToken.jti==jti)
        )
        blacklisted = result.scalar_one_or_none()
       
        if blacklisted:
            return None
        return {
            "user_id":payload["user_id"],
            "role":payload["role"],
            "jti":jti
        }
    except JWTError:
        return None
    
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp":expire,
                      "type":"refresh"
    })
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

