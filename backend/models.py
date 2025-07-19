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
    context: Optional[Dict[str, Any]] = None

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

# Auto Trading Models
class AutoTradingSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    enabled: bool = False
    max_trade_amount: float = 1000.0  # Maximum ZAR per trade
    daily_limit: float = 5000.0  # Maximum ZAR traded per day
    allowed_assets: List[str] = ["BTC", "ETH", "ADA", "XRP", "SOL"]
    risk_level: str = "medium"  # low, medium, high
    stop_loss_percent: float = 5.0  # Auto stop loss at 5%
    take_profit_percent: float = 10.0  # Auto take profit at 10%
    auto_rebalance: bool = False
    trading_hours: Dict[str, Any] = {"start": "08:00", "end": "22:00", "timezone": "Africa/Johannesburg"}
    conditions: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AutoTradeLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    trade_type: str  # 'buy', 'sell', 'stop_loss', 'take_profit'
    asset: str
    amount: float
    price: float
    value: float
    reason: str
    success: bool
    luno_order_id: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)

class AutoTradingSettingsCreate(BaseModel):
    enabled: bool = False
    max_trade_amount: float = 1000.0
    daily_limit: float = 5000.0
    allowed_assets: List[str] = ["BTC", "ETH", "ADA", "XRP", "SOL"]
    risk_level: str = "medium"
    stop_loss_percent: float = 5.0
    take_profit_percent: float = 10.0
    auto_rebalance: bool = False
    trading_hours: Dict[str, Any] = {"start": "08:00", "end": "22:00", "timezone": "Africa/Johannesburg"}
    conditions: Dict[str, Any] = {}

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

# Technical Analysis Models
class TechnicalIndicators(BaseModel):
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    bollinger_bands: Optional[Dict[str, float]] = None
    moving_averages: Optional[Dict[str, float]] = None
    support_resistance: Optional[Dict[str, float]] = None
    stochastic: Optional[Dict[str, float]] = None

class TradingSignal(BaseModel):
    type: str  # 'BUY', 'SELL', 'HOLD'
    reason: str
    strength: str  # 'weak', 'medium', 'strong'
    indicator: str
    confidence: float = 0.5

class TrendAnalysis(BaseModel):
    trend: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0.0 to 1.0
    signals: List[str]
    bullish_signals: float
    bearish_signals: float

class TechnicalAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    current_price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trend_analysis: TrendAnalysis
    technical_indicators: TechnicalIndicators
    trading_signals: List[TradingSignal]
    recommendation: Dict[str, Any]
    data_points: int

class PortfolioTechnicalAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_total: float
    analyzed_assets: int
    asset_analysis: List[TechnicalAnalysisResult]
    portfolio_insights: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class TechnicalStrategy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    indicators: List[str]
    rules: List[Dict[str, Any]]
    risk_parameters: Dict[str, float]
    created_at: datetime = Field(default_factory=datetime.utcnow)