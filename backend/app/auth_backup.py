from datetime import datetime, timedelta
from typing import Optional, Union, cast
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.database import get_management_db
from app import models
from app.models_company import User as CompanyUser
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    management_db: Session = Depends(get_management_db)
) -> Union[models.SystemUser, CompanyUser]:
    """Get current authenticated user (system user or company user)"""
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # First check if this is a system user
    system_user = management_db.query(models.SystemUser).filter(
        models.SystemUser.username == username
    ).first()
    
    if system_user:
        if not bool(system_user.is_active):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive system user"
            )
        return system_user
    
    # If not a system user, check company databases
    companies = management_db.query(models.Company).filter(
        models.Company.is_active == True
    ).all()
    
    for company in companies:
        try:
            from app.database import get_company_db
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            user = company_db.query(CompanyUser).filter(
                CompanyUser.username == username
            ).first()
            
            if user:
                if not bool(user.is_active):
                    company_db.close()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Inactive user"
                    )
                
                # Add company information to user object for compatibility
                user.company_id = company.id  # type: ignore
                user.company = company  # type: ignore
                company_db.close()
                return user
            
            company_db.close()
            
        except Exception:
            continue
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_system_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_management_db)
) -> models.SystemUser:
    """Get current authenticated system user from management database"""
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if this is a system user in management database
    system_user = db.query(models.SystemUser).filter(
        models.SystemUser.username == username
    ).first()
    
    if system_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="System user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not bool(system_user.is_active):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive system user"
        )
    
    return system_user

async def get_current_company_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    management_db: Session = Depends(get_management_db)
) -> CompanyUser:
    """Get current authenticated company user (not system user)"""
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # First ensure this is NOT a system user
    system_user = management_db.query(models.SystemUser).filter(
        models.SystemUser.username == username
    ).first()
    
    if system_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System users cannot access company resources"
        )
    
    # Find company user
    companies = management_db.query(models.Company).filter(
        models.Company.is_active == True
    ).all()
    
    for company in companies:
        try:
            from app.database import get_company_db
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            user = company_db.query(CompanyUser).filter(
                CompanyUser.username == username
            ).first()
            
            if user:
                if not bool(user.is_active):
                    company_db.close()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Inactive user"
                    )
                
                # Add company information to user object
                user.company_id = company.id  # type: ignore
                user.company = company  # type: ignore
                company_db.close()
                return user

            company_db.close()
            
        except Exception:
            continue
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Company user not found",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_admin_user(
    current_user: CompanyUser = Depends(get_current_company_user)
) -> CompanyUser:
    """Get current user and verify admin privileges (company level)"""
    if current_user.role not in ["hr_admin", "hr_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user 