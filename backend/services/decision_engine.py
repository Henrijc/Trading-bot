"""
Decision Engine for AI Crypto Trading Coach
Final intelligence layer that guides AI trading actions based on portfolio goals

This engine evaluates trade signals from FreqAI against user targets and portfolio status
to make intelligent trading decisions aligned with financial objectives.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass

# Import existing services
from services.luno_service import LunoService
from services.target_service import TargetService
from services.freqtrade_service import FreqtradeService

logger = logging.getLogger(__name__)

class DecisionResult(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    HOLD = "hold"
    REDUCE_POSITION = "reduce_position"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class TradeSignal:
    """Represents a trade signal from FreqAI"""
    pair: str
    action: str  # 'buy' or 'sell'
    confidence: float  # 0.0 to 1.0
    signal_strength: str  # 'weak', 'medium', 'strong'
    direction: str  # 'bullish', 'bearish', 'neutral'
    amount: float
    predicted_return: Optional[float] = None
    timestamp: str = None

@dataclass
class PortfolioStatus:
    """Current portfolio status"""
    total_value_zar: float
    assets: Dict[str, Dict[str, float]]
    monthly_performance: float
    weekly_performance: float
    days_in_month: int
    risk_exposure: float

@dataclass
class DecisionContext:
    """Complete context for decision making"""
    portfolio: PortfolioStatus
    targets: Dict[str, Any]
    signal: TradeSignal
    risk_level: RiskLevel
    market_conditions: Optional[Dict[str, Any]] = None

@dataclass
class DecisionEngineResult:
    """Result of decision engine evaluation"""
    decision: DecisionResult
    confidence: float
    reasoning: str
    recommended_amount: Optional[float] = None
    risk_assessment: str = ""
    conditions: List[str] = None

class DecisionEngine:
    """
    Core decision engine that evaluates trade signals against portfolio goals
    """
    
    def __init__(self):
        self.luno_service = LunoService()
        self.target_service = TargetService()
        self.freqtrade_service = FreqtradeService()
        
        # Risk management parameters
        self.MAX_RISK_PER_TRADE = 0.04  # 4% maximum risk per trade
        self.MAX_PORTFOLIO_RISK = 0.20  # 20% maximum portfolio exposure
        self.MIN_CONFIDENCE_THRESHOLD = 0.60  # Minimum confidence for trades
        self.PROTECTED_XRP_AMOUNT = 1000  # XRP long-term hold protection
        
        logger.info("Decision Engine initialized")
    
    async def evaluate_trade_signal(self, signal: TradeSignal) -> DecisionEngineResult:
        """
        Main decision evaluation method
        Implements the core logic: evaluate signal against portfolio status and targets
        """
        try:
            # Step 1: Gather complete context
            context = await self._gather_decision_context(signal)
            
            # Step 2: Apply decision rules
            result = await self._apply_decision_rules(context)
            
            logger.info(f"Decision for {signal.pair} {signal.action}: {result.decision.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error in decision evaluation: {e}")
            return DecisionEngineResult(
                decision=DecisionResult.REJECT,
                confidence=0.0,
                reasoning=f"Decision engine error: {str(e)}",
                risk_assessment="HIGH - System error"
            )
    
    async def _gather_decision_context(self, signal: TradeSignal) -> DecisionContext:
        """Gather all necessary context for decision making"""
        
        # Fetch current portfolio status
        portfolio_data = await self.luno_service.get_portfolio_data()
        portfolio_status = self._parse_portfolio_data(portfolio_data)
        
        # Fetch user targets
        targets = await self.target_service.get_target_settings()
        
        # Assess risk level
        risk_level = self._assess_current_risk_level(portfolio_status, signal)
        
        return DecisionContext(
            portfolio=portfolio_status,
            targets=targets,
            signal=signal,
            risk_level=risk_level
        )
    
    async def _apply_decision_rules(self, context: DecisionContext) -> DecisionEngineResult:
        """
        Apply intelligent decision rules based on portfolio status and targets
        """
        
        # Rule 1: Portfolio Performance vs Targets
        performance_rule = self._evaluate_performance_rule(context)
        
        # Rule 2: Signal Quality and Confidence
        signal_rule = self._evaluate_signal_quality_rule(context)
        
        # Rule 3: Risk Management
        risk_rule = self._evaluate_risk_management_rule(context)
        
        # Rule 4: Asset-Specific Rules (XRP protection, etc.)
        asset_rule = self._evaluate_asset_specific_rules(context)
        
        # Combine all rule results
        return self._combine_rule_results(context, [
            performance_rule, signal_rule, risk_rule, asset_rule
        ])
    
    def _evaluate_performance_rule(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Rule 1: Portfolio Performance vs Targets
        - If above target and signal is sell → more likely to approve
        - If below target and signal is high-confidence buy → more likely to approve
        """
        portfolio = context.portfolio
        targets = context.targets
        signal = context.signal
        
        monthly_target = targets.get('monthly_target', 8000)  # R8,000 default
        current_performance = portfolio.monthly_performance
        target_progress = current_performance / monthly_target if monthly_target > 0 else 0
        
        reasoning = []
        score = 0.5  # Neutral starting point
        
        if target_progress >= 1.0:  # Above target
            reasoning.append(f"Portfolio above monthly target ({target_progress:.1%})")
            if signal.action == 'sell':
                score += 0.3  # Favor profit-taking when above target
                reasoning.append("Favoring sell signal - profit taking strategy")
            elif signal.action == 'buy':
                score -= 0.1  # Less aggressive buying when above target
                reasoning.append("Reducing buy enthusiasm - already above target")
        
        elif target_progress < 0.5:  # Significantly below target
            reasoning.append(f"Portfolio below target ({target_progress:.1%})")
            if signal.action == 'buy' and signal.confidence > 0.7:
                score += 0.4  # Aggressive buying when below target with high confidence
                reasoning.append("Favoring high-confidence buy - catching up to target")
            elif signal.action == 'sell':
                score -= 0.2  # Avoid selling when below target unless necessary
                reasoning.append("Reducing sell tendency - need to reach target")
        
        return {
            'name': 'performance_rule',
            'score': score,
            'reasoning': reasoning,
            'target_progress': target_progress
        }
    
    def _evaluate_signal_quality_rule(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Rule 2: Signal Quality and Confidence
        Higher confidence and stronger signals get higher scores
        """
        signal = context.signal
        reasoning = []
        score = 0.0
        
        # Confidence scoring
        if signal.confidence >= 0.8:
            score += 0.4
            reasoning.append(f"Very high confidence ({signal.confidence:.1%})")
        elif signal.confidence >= 0.7:
            score += 0.3
            reasoning.append(f"High confidence ({signal.confidence:.1%})")
        elif signal.confidence >= 0.6:
            score += 0.1
            reasoning.append(f"Moderate confidence ({signal.confidence:.1%})")
        else:
            score -= 0.2
            reasoning.append(f"Low confidence ({signal.confidence:.1%})")
        
        # Signal strength scoring
        if signal.signal_strength == 'strong':
            score += 0.2
            reasoning.append("Strong signal strength")
        elif signal.signal_strength == 'medium':
            score += 0.1
            reasoning.append("Medium signal strength")
        else:
            score -= 0.1
            reasoning.append("Weak signal strength")
        
        return {
            'name': 'signal_quality_rule',
            'score': score,
            'reasoning': reasoning,
            'confidence': signal.confidence
        }
    
    def _evaluate_risk_management_rule(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Rule 3: Risk Management
        Enforce position sizing and risk limits
        """
        portfolio = context.portfolio
        signal = context.signal
        reasoning = []
        score = 0.5  # Start neutral
        
        # Check portfolio risk exposure
        if portfolio.risk_exposure > 0.15:  # Above 15% portfolio risk
            score -= 0.3
            reasoning.append(f"High portfolio risk exposure ({portfolio.risk_exposure:.1%})")
        elif portfolio.risk_exposure < 0.05:  # Below 5% risk
            score += 0.1
            reasoning.append(f"Low portfolio risk exposure ({portfolio.risk_exposure:.1%})")
        
        # Validate trade size against risk limits
        max_trade_value = portfolio.total_value_zar * self.MAX_RISK_PER_TRADE
        if signal.amount * 1000 > max_trade_value:  # Assuming price in thousands
            score -= 0.4
            reasoning.append(f"Trade size exceeds 4% risk limit")
        
        # Check if this would exceed maximum portfolio exposure
        current_exposure = portfolio.assets.get(signal.pair.split('/')[0], {}).get('zar_value', 0)
        max_exposure = portfolio.total_value_zar * self.MAX_PORTFOLIO_RISK
        
        if signal.action == 'buy' and current_exposure > max_exposure * 0.8:
            score -= 0.2
            reasoning.append(f"Approaching maximum exposure for {signal.pair}")
        
        return {
            'name': 'risk_management_rule',
            'score': score,
            'reasoning': reasoning,
            'risk_exposure': portfolio.risk_exposure
        }
    
    def _evaluate_asset_specific_rules(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Rule 4: Asset-Specific Rules
        Handle XRP protection and other asset-specific logic
        """
        signal = context.signal
        portfolio = context.portfolio
        reasoning = []
        score = 0.5  # Start neutral
        
        # XRP Protection Rule
        if signal.pair.startswith('XRP'):
            current_xrp = portfolio.assets.get('XRP', {}).get('balance', 0)
            
            if signal.action == 'sell' and current_xrp <= self.PROTECTED_XRP_AMOUNT:
                score -= 0.8  # Heavily penalize selling protected XRP
                reasoning.append(f"XRP protection: {self.PROTECTED_XRP_AMOUNT} XRP reserved for long-term hold")
            elif signal.action == 'sell' and current_xrp > self.PROTECTED_XRP_AMOUNT * 1.2:
                score += 0.1  # Allow selling excess XRP
                reasoning.append("XRP sell allowed - above protected amount")
            elif signal.action == 'buy':
                score += 0.1  # Favor building XRP position
                reasoning.append("XRP buy favored for long-term position")
        
        # BTC/ETH major pairs - generally more stable
        if signal.pair in ['BTC/ZAR', 'ETH/ZAR']:
            score += 0.1
            reasoning.append(f"Major pair {signal.pair} - additional stability weight")
        
        return {
            'name': 'asset_specific_rule',
            'score': score,
            'reasoning': reasoning
        }
    
    def _combine_rule_results(self, context: DecisionContext, rule_results: List[Dict[str, Any]]) -> DecisionEngineResult:
        """
        Combine all rule results into final decision
        """
        total_score = sum(rule['score'] for rule in rule_results)
        average_score = total_score / len(rule_results)
        
        # Collect all reasoning
        all_reasoning = []
        for rule in rule_results:
            all_reasoning.extend(rule['reasoning'])
        
        # Make final decision based on combined score
        if average_score >= 0.7:
            decision = DecisionResult.APPROVE
            confidence = min(0.9, average_score)
        elif average_score >= 0.3:
            decision = DecisionResult.HOLD
            confidence = 0.5
        else:
            decision = DecisionResult.REJECT
            confidence = max(0.1, 1.0 - average_score)
        
        # Calculate recommended amount based on risk management
        recommended_amount = self._calculate_recommended_amount(context, decision)
        
        # Risk assessment
        risk_assessment = self._generate_risk_assessment(context, average_score)
        
        return DecisionEngineResult(
            decision=decision,
            confidence=confidence,
            reasoning="; ".join(all_reasoning),
            recommended_amount=recommended_amount,
            risk_assessment=risk_assessment,
            conditions=self._generate_conditions(context, decision)
        )
    
    def _calculate_recommended_amount(self, context: DecisionContext, decision: DecisionResult) -> Optional[float]:
        """Calculate recommended trade amount based on risk management"""
        if decision != DecisionResult.APPROVE:
            return None
        
        portfolio = context.portfolio
        signal = context.signal
        
        # Base amount on 4% risk rule
        max_trade_value = portfolio.total_value_zar * self.MAX_RISK_PER_TRADE
        
        # Adjust based on confidence
        confidence_multiplier = min(1.0, signal.confidence * 1.2)
        
        # Calculate recommended amount
        recommended_value = max_trade_value * confidence_multiplier
        
        # Convert to asset amount (simplified - assumes price data available)
        # In real implementation, would fetch current price
        estimated_price = 50000  # Placeholder for BTC price
        recommended_amount = recommended_value / estimated_price
        
        return recommended_amount
    
    def _generate_risk_assessment(self, context: DecisionContext, score: float) -> str:
        """Generate risk assessment string"""
        if score >= 0.7:
            return "LOW - High confidence with good portfolio alignment"
        elif score >= 0.5:
            return "MEDIUM - Moderate confidence with acceptable risk"
        elif score >= 0.3:
            return "MEDIUM-HIGH - Lower confidence, increased monitoring needed"
        else:
            return "HIGH - Low confidence or high risk factors"
    
    def _generate_conditions(self, context: DecisionContext, decision: DecisionResult) -> List[str]:
        """Generate conditions for trade execution"""
        conditions = []
        
        if decision == DecisionResult.APPROVE:
            conditions.append("Execute with 4% stop-loss")
            conditions.append("Monitor position size limits")
            
            if context.signal.pair.startswith('XRP'):
                conditions.append(f"Maintain {self.PROTECTED_XRP_AMOUNT} XRP long-term hold")
            
            if context.signal.confidence < 0.7:
                conditions.append("Use smaller position size due to moderate confidence")
        
        return conditions
    
    def _parse_portfolio_data(self, portfolio_data: Dict[str, Any]) -> PortfolioStatus:
        """Parse portfolio data from Luno service into PortfolioStatus"""
        # Simplified parsing - in real implementation would handle full portfolio structure
        total_value = portfolio_data.get('total_value_zar', 0)
        assets = portfolio_data.get('assets', {})
        
        # Calculate performance metrics (simplified)
        monthly_performance = portfolio_data.get('monthly_performance', 0)
        weekly_performance = portfolio_data.get('weekly_performance', 0)
        
        # Calculate risk exposure (simplified)
        risk_exposure = 0.1  # Placeholder calculation
        
        return PortfolioStatus(
            total_value_zar=total_value,
            assets=assets,
            monthly_performance=monthly_performance,
            weekly_performance=weekly_performance,
            days_in_month=datetime.now().day,
            risk_exposure=risk_exposure
        )
    
    def _assess_current_risk_level(self, portfolio: PortfolioStatus, signal: TradeSignal) -> RiskLevel:
        """Assess current overall risk level"""
        if portfolio.risk_exposure > 0.15:
            return RiskLevel.HIGH
        elif portfolio.risk_exposure > 0.10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def get_decision_engine_status(self) -> Dict[str, Any]:
        """Get current decision engine status and configuration"""
        return {
            "status": "active",
            "version": "1.0",
            "max_risk_per_trade": self.MAX_RISK_PER_TRADE,
            "max_portfolio_risk": self.MAX_PORTFOLIO_RISK,
            "min_confidence_threshold": self.MIN_CONFIDENCE_THRESHOLD,
            "protected_xrp_amount": self.PROTECTED_XRP_AMOUNT,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def simulate_decision(self, pair: str, action: str, amount: float, confidence: float) -> DecisionEngineResult:
        """Simulate a decision without executing - useful for testing and analysis"""
        
        # Create test signal
        test_signal = TradeSignal(
            pair=pair,
            action=action,
            confidence=confidence,
            signal_strength="medium" if confidence > 0.6 else "weak",
            direction="bullish" if action == "buy" else "bearish",
            amount=amount,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Evaluate the decision
        return await self.evaluate_trade_signal(test_signal)