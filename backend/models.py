from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Chat Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatMessageCreate(BaseModel):
    session_id: str
    role: str
    message: str

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)

# Portfolio Models
class CryptoHolding(BaseModel):
    symbol: str
    name: str
    amount: float
    current_price: float
    value: float
    change_24h: float
    allocation: float

class Portfolio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    total_value: float
    currency: str = "ZAR"
    holdings: List[CryptoHolding]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Market Data Models
class CryptoMarketData(BaseModel):
    symbol: str
    name: str
    price: float
    change_24h: float
    volume: float
    market_cap: float
    trend: str  # 'up' or 'down'
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Trading Strategy Models
class TradingAction(BaseModel):
    type: str  # 'BUY', 'SELL', 'TAKE_PROFIT', 'STOP_LOSS'
    asset: str
    amount: str
    price: str
    reasoning: str

class KeyLevels(BaseModel):
    support: str
    resistance: str
    target: str

class DailyStrategy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    main_recommendation: str
    risk_level: str
    expected_return: str
    timeframe: str
    key_levels: KeyLevels
    actions: List[TradingAction]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Weekly Targets Models
class WeeklyMilestone(BaseModel):
    day: str
    target: float
    achieved: float
    status: str  # 'exceeded', 'below', 'pending'

class WeeklyTargets(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week_of: str
    target: float
    achieved: float
    remaining: float
    days_left: int
    daily_required: float
    progress: float
    milestones: List[WeeklyMilestone]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Risk Management Models
class RiskMetrics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    risk_score: float
    max_risk: float = 10.0
    portfolio_var: float  # Value at Risk percentage
    sharpe_ratio: float
    max_drawdown: float
    diversification_score: float
    recommendations: List[str]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

# User Settings Models
class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    monthly_target: float = 100000.0
    risk_tolerance: str = "medium"  # 'low', 'medium', 'high'
    preferred_cryptocurrencies: List[str] = ["BTC", "ETH", "LTC", "XRP"]
    notification_preferences: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# News Models
class NewsItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    impact: str  # 'bullish', 'bearish', 'neutral'
    source: str
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)