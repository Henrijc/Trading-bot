import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for the backend
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Corrected imports for services, now that /app is the root and backend is a subfolder
# All services are accessed via 'backend.services.<module_name>'
from backend.services.ai_service import AICoachService
from backend.services.authentication_service import auth_router, SecurityService
from backend.services.backtest_api_service import backtest_router
from backend.services.decision_engine import DecisionEngine
from backend.services.freqtrade_service import FreqtradeService
from backend.services.historical_data_service import HistoricalDataService
from backend.services.live_trading_service import live_trading_router
from backend.services.luno_service import LunoService
from backend.services.security_monitoring_service import SecurityMonitoringService
from backend.services.security_service import SecurityScannerService
from backend.services.semi_auto_trade_service import SemiAutoTradeService
from backend.services.target_service import TargetService
from backend.services.technical_analysis_service import TechnicalAnalysisService
from backend.services.trading_campaign_service import TradingCampaignService


# Initialize services
security_service = SecurityService()
security_scanner = SecurityScannerService()
historical_data_service = HistoricalDataService()
technical_analysis_service = TechnicalAnalysisService()
luno_service = LunoService()
freqtrade_service = FreqtradeService()
ai_coach_service = AICoachService()
decision_engine = DecisionEngine()
# live_trading_service = LiveTradingService()  # Commented out - using router instead
semi_auto_trade_service = SemiAutoTradeService()
target_service = TargetService()
trading_campaign_service = TradingCampaignService()


# FastAPI app
app = FastAPI(title="Crypto Trading Coach API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://34.121.6.206:3000", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(backtest_router, prefix="/backtest", tags=["Backtesting"])

# Define API routes - using service instances
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Backend API is running"}

# You'll need to define more routes here that uses the services

@app.on_event("startup")
async def startup_event():
    logger.info("Crypto Trading Coach API started")
    # You might want to initialize some services or connections here
    security_scanner.run_initial_scan()
    logger.info("Initial security scan completed.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Crypto Trading Coach API is shutting down")