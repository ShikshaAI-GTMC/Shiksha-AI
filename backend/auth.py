import os
from datetime import datetime,timedelta,timezone
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import JWTError,jwt
from passlib.context import CryptContext
from database import db

pwd_context=CryptContext(schemes=['bcrypt'],deprecated='auto')
security=HTTPBearer()
SECRET_KEY=os.getenv('JWT_SECRET','change-this-development-secret-before-production')
ALGORITHM='HS256'
def hash_password(value:str)->str:return pwd_context.hash(value)
def verify_password(plain:str,hashed:str)->bool:return pwd_context.verify(plain,hashed)
def create_token(user_id:str)->str:return jwt.encode({'sub':user_id,'exp':datetime.now(timezone.utc)+timedelta(days=7)},SECRET_KEY,algorithm=ALGORITHM)
async def current_user(credentials:HTTPAuthorizationCredentials=Depends(security)):
    try: uid=jwt.decode(credentials.credentials,SECRET_KEY,algorithms=[ALGORITHM]).get('sub')
    except JWTError: uid=None
    if not uid: raise HTTPException(status.HTTP_401_UNAUTHORIZED,'Invalid or expired access token')
    from bson import ObjectId
    user=await db.users.find_one({'_id':ObjectId(uid)})
    if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED,'User not found')
    return user
