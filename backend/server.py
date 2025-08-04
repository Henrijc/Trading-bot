import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple imports - no complex paths
from services.ai_service import AICoachService
from services.luno_service import LunoService
from services.technical_analysis_service import TechnicalAnalysisService

# Initialize services
ai_service = AICoachService()
luno_service = LunoService()
ta_service = TechnicalAnalysisService()

# FastAPI app
app = FastAPI(title="Crypto Trading Coach API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "message": "Backend API is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Crypto Trading Coach API started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Crypto Trading Coach API is shutting down")