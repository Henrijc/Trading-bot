import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional

# Corrected imports for services
from backend.services.security_service import SecurityService
from backend.services.database_service import get_database_client

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class AuthenticationService:
    def __init__(self):
        self.security_service = SecurityService()
        self.db_client = get_database_client()
        logger.info("AuthenticationService initialized.")

    async def register_user(self, username, password):
        """Registers a new user after hashing the password."""
        if await self.db_client.get_user(username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
        hashed_password = self.security_service.hash_password(password)
        await self.db_client.create_user(username, hashed_password)
        logger.info(f"User {username} registered successfully.")
        return {"message": "User registered successfully"}

    async def authenticate_user(self, username, password):
        """Authenticates a user and returns a JWT token if successful."""
        user = await self.db_client.get_user(username)
        if not user or not self.security_service.verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=30)  # You can adjust this
        access_token = self.security_service.create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        logger.info(f"User {username} authenticated successfully.")
        return {"access_token": access_token, "token_type": "bearer"}

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        """Retrieves the current authenticated user from the token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = self.security_service.decode_access_token(token)
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            user = await self.db_client.get_user(username)
            if user is None:
                raise credentials_exception
            return user
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise credentials_exception

# Initialize the service
auth_service = AuthenticationService()

# Authentication router
auth_router = APIRouter()

@auth_router.post("/register")
async def register(username: str, password: str):
    return await auth_service.register_user(username, password)

@auth_router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return await auth_service.authenticate_user(form_data.username, form_data.password)

@auth_router.get("/users/me")
async def read_users_me(current_user: dict = Depends(auth_service.get_current_user)):
    return current_user