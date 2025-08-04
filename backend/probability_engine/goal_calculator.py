import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import math

logger = logging.getLogger(__name__)

class GoalProbabilityCalculator:
    """
    Advanced probability calculator for trading goal achievement
    Uses statistical modeling and machine learning to predict success rates
    """
    
    def __init__(self):
        self.confidence_threshold = 0.75
        self.min_data_points = 30
        
    def calculate_daily_probability(self, trades: List[Dict], target_zar: float = 1000) -> Dict[str, Any]:
        """
        Calculate probability of achieving daily profit target
        
        Args:
            trades: List of trade records
            target_zar: Daily target in ZAR
            
        Returns:
            Dict with probability metrics
        """
        try:
            if len(trades) < self.min_data_points:
                return {
                    "probability": 0.5,
                    "confidence": "low",
                    "message": "Insufficient data for accurate prediction",
                    "required_trades": max(0, self.min_data_points - len(trades))
                }
                
            # Convert trades to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # Group by day and calculate daily P&L
            daily_pnl = df.groupby('date')['profit_zar'].sum().reset_index()
            daily_returns = daily_pnl['profit_zar'].values
            
            # Statistical analysis
            mean_daily = np.mean(daily_returns)
            std_daily = np.std(daily_returns)
            
            # Calculate probability using normal distribution
            if std_daily > 0:
                z_score = (target_zar - mean_daily) / std_daily
                probability = 1 - stats.norm.cdf(z_score)
            else:
                probability = 1.0 if mean_daily >= target_zar else 0.0
                
            # Trend analysis
            trend_factor = self._calculate_trend_factor(daily_returns)
            
            # Volatility adjustment
            volatility_factor = self._calculate_volatility_factor(daily_returns, target_zar)
            
            # Combine factors
            adjusted_probability = probability * trend_factor * volatility_factor
            adjusted_probability = np.clip(adjusted_probability, 0.01, 0.99)
            
            # Win rate analysis
            win_rate = len(daily_returns[daily_returns >= target_zar]) / len(daily_returns)
            
            # Confidence calculation
            confidence_score = self._calculate_confidence(daily_returns, len(trades))
            
            return {
                "probability": round(adjusted_probability, 4),
                "confidence": self._get_confidence_level_string(confidence_score),
                "confidence_score": round(confidence_score, 3),
                "statistics": {
                    "mean_daily_pnl": round(mean_daily, 2),
                    "std_daily_pnl": round(std_daily, 2),
                    "win_rate": round(win_rate, 3),
                    "days_analyzed": len(daily_returns),
                    "target_zar": target_zar
                },
                "factors": {
                    "base_probability": round(probability, 4),
                    "trend_factor": round(trend_factor, 3),
                    "volatility_factor": round(volatility_factor, 3)
                },
                "recommendation": self._generate_recommendation(adjusted_probability, mean_daily, target_zar)
            }
            
        except Exception as e:
            logger.error(f"Daily probability calculation failed: {e}")
            return {
                "probability": 0.5,
                "confidence": "error",
                "message": f"Calculation error: {str(e)}"
            }
            
    def calculate_weekly_probability(self, trades: List[Dict], target_zar: float = 7000) -> Dict[str, Any]:
        """Calculate probability of achieving weekly profit target"""
        try:
            if len(trades) < self.min_data_points:
                return {"probability": 0.5, "confidence": "low", "message": "Insufficient data"}
                
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['week'] = df['timestamp'].dt.isocalendar().week
            df['year'] = df['timestamp'].dt.year
            
            # Group by week and calculate weekly P&L
            weekly_pnl = df.groupby(['year', 'week'])['profit_zar'].sum().reset_index()
            weekly_returns = weekly_pnl['profit_zar'].values
            
            if len(weekly_returns) < 4:  # Need at least 4 weeks of data
                return {"probability": 0.5, "confidence": "low", "message": "Need more weekly data"}
                
            mean_weekly = np.mean(weekly_returns)
            std_weekly = np.std(weekly_returns)
            
            if std_weekly > 0:
                z_score = (target_zar - mean_weekly) / std_weekly
                probability = 1 - stats.norm.cdf(z_score)
            else:
                probability = 1.0 if mean_weekly >= target_zar else 0.0
                
            # Apply trend and volatility factors
            trend_factor = self._calculate_trend_factor(weekly_returns)
            volatility_factor = self._calculate_volatility_factor(weekly_returns, target_zar)
            
            adjusted_probability = probability * trend_factor * volatility_factor
            adjusted_probability = np.clip(adjusted_probability, 0.01, 0.99)
            
            return {
                "probability": round(adjusted_probability, 4),
                "confidence": self._get_confidence_level_string(self._calculate_confidence(weekly_returns, len(trades))),
                "statistics": {
                    "mean_weekly_pnl": round(mean_weekly, 2),
                    "std_weekly_pnl": round(std_weekly, 2),
                    "weeks_analyzed": len(weekly_returns),
                    "target_zar": target_zar
                }
            }
            
        except Exception as e:
            logger.error(f"Weekly probability calculation failed: {e}")
            return {"probability": 0.5, "confidence": "error", "message": str(e)}
            
    def calculate_monthly_probability(self, trades: List[Dict], target_zar: float = 30000) -> Dict[str, Any]:
        """Calculate probability of achieving monthly profit target"""
        try:
            if len(trades) < self.min_data_points:
                return {"probability": 0.5, "confidence": "low", "message": "Insufficient data"}
                
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['month'] = df['timestamp'].dt.month
            df['year'] = df['timestamp'].dt.year
            
            # Group by month and calculate monthly P&L
            monthly_pnl = df.groupby(['year', 'month'])['profit_zar'].sum().reset_index()
            monthly_returns = monthly_pnl['profit_zar'].values
            
            if len(monthly_returns) < 2:  # Need at least 2 months of data
                # Use daily data to estimate monthly performance
                return self._estimate_monthly_from_daily(trades, target_zar)
                
            mean_monthly = np.mean(monthly_returns)
            std_monthly = np.std(monthly_returns)
            
            if std_monthly > 0:
                z_score = (target_zar - mean_monthly) / std_monthly
                probability = 1 - stats.norm.cdf(z_score)
            else:
                probability = 1.0 if mean_monthly >= target_zar else 0.0
                
            trend_factor = self._calculate_trend_factor(monthly_returns)
            volatility_factor = self._calculate_volatility_factor(monthly_returns, target_zar)
            
            adjusted_probability = probability * trend_factor * volatility_factor
            adjusted_probability = np.clip(adjusted_probability, 0.01, 0.99)
            
            return {
                "probability": round(adjusted_probability, 4),
                "confidence": self._get_confidence_level_string(self._calculate_confidence(monthly_returns, len(trades))),
                "statistics": {
                    "mean_monthly_pnl": round(mean_monthly, 2),
                    "std_monthly_pnl": round(std_monthly, 2),
                    "months_analyzed": len(monthly_returns),
                    "target_zar": target_zar
                }
            }
            
        except Exception as e:
            logger.error(f"Monthly probability calculation failed: {e}")
            return {"probability": 0.5, "confidence": "error", "message": str(e)}
            
    def _estimate_monthly_from_daily(self, trades: List[Dict], target_zar: float) -> Dict[str, Any]:
        """Estimate monthly probability from daily data"""
        try:
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            daily_pnl = df.groupby('date')['profit_zar'].sum().reset_index()
            daily_returns = daily_pnl['profit_zar'].values
            
            if len(daily_returns) < 10:
                return {"probability": 0.5, "confidence": "very_low", "message": "Insufficient data"}
                
            # Estimate monthly performance (22 trading days per month)
            trading_days_per_month = 22
            mean_daily = np.mean(daily_returns)
            std_daily = np.std(daily_returns)
            
            # Monthly statistics (assuming independence)
            estimated_monthly_mean = mean_daily * trading_days_per_month
            estimated_monthly_std = std_daily * np.sqrt(trading_days_per_month)
            
            if estimated_monthly_std > 0:
                z_score = (target_zar - estimated_monthly_mean) / estimated_monthly_std
                probability = 1 - stats.norm.cdf(z_score)
            else:
                probability = 1.0 if estimated_monthly_mean >= target_zar else 0.0
                
            return {
                "probability": round(np.clip(probability, 0.01, 0.99), 4),
                "confidence": "estimated",
                "message": "Estimated from daily data",
                "statistics": {
                    "estimated_monthly_mean": round(estimated_monthly_mean, 2),
                    "estimated_monthly_std": round(estimated_monthly_std, 2),
                    "based_on_days": len(daily_returns),
                    "target_zar": target_zar
                }
            }
            
        except Exception as e:
            logger.error(f"Monthly estimation failed: {e}")
            return {"probability": 0.5, "confidence": "error", "message": str(e)}
            
    def _calculate_trend_factor(self, returns: np.ndarray) -> float:
        """Calculate trend factor based on recent performance"""
        try:
            if len(returns) < 5:
                return 1.0
                
            # Linear regression on recent data
            x = np.arange(len(returns)).reshape(-1, 1)
            y = returns
            
            model = LinearRegression()
            model.fit(x, y)
            
            slope = model.coef_[0]
            
            # Convert slope to factor (positive trend increases probability)
            if slope > 0:
                trend_factor = 1.0 + min(slope / np.mean(returns), 0.3)  # Cap at 30% boost
            else:
                trend_factor = 1.0 + max(slope / np.mean(returns), -0.3)  # Cap at 30% reduction
                
            return np.clip(trend_factor, 0.5, 1.5)
            
        except Exception as e:
            logger.error(f"Trend factor calculation failed: {e}")
            return 1.0
            
    def _calculate_volatility_factor(self, returns: np.ndarray, target: float) -> float:
        """Calculate volatility adjustment factor"""
        try:
            if len(returns) < 3:
                return 1.0
                
            mean_return = np.mean(returns)
            volatility = np.std(returns)
            
            if mean_return == 0 or volatility == 0:
                return 1.0
                
            # Coefficient of variation
            cv = volatility / abs(mean_return)
            
            # Lower volatility increases probability if mean > target
            # Higher volatility decreases probability
            if mean_return >= target:
                volatility_factor = 1.0 / (1.0 + cv)
            else:
                volatility_factor = 1.0 + (cv * 0.5)  # High volatility can help if underperforming
                
            return np.clip(volatility_factor, 0.5, 1.5)
            
        except Exception as e:
            logger.error(f"Volatility factor calculation failed: {e}")
            return 1.0
            
    def _calculate_confidence(self, returns: np.ndarray, total_trades: int) -> float:
        """Calculate confidence score based on data quality"""
        try:
            data_points_factor = min(len(returns) / self.min_data_points, 1.0)
            trade_count_factor = min(total_trades / 100, 1.0)
            
            # Consistency factor (lower standard deviation relative to mean = higher confidence)
            if len(returns) > 1:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                consistency_factor = 1.0 / (1.0 + (std_return / max(abs(mean_return), 1.0)))
            else:
                consistency_factor = 0.5
                
            confidence = (data_points_factor + trade_count_factor + consistency_factor) / 3
            return np.clip(confidence, 0.1, 1.0)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
            
    def _get_confidence_level_string(self, confidence_score: float) -> str:
        """Convert confidence score to string"""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        elif confidence_score >= 0.4:
            return "low"
        else:
            return "very_low"
            
    def _generate_recommendation(self, probability: float, mean_daily: float, target: float) -> str:
        """Generate actionable recommendation"""
        if probability >= 0.8:
            return "Excellent probability of success. Current strategy is performing well."
        elif probability >= 0.6:
            return "Good probability of success. Consider minor strategy optimizations."
        elif probability >= 0.4:
            if mean_daily < target * 0.5:
                return "Low probability. Significant strategy changes needed to reach target."
            else:
                return "Moderate probability. Focus on reducing losses and improving win rate."
        else:
            return "Very low probability. Major strategy overhaul recommended."
            
    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate percentage"""
        try:
            if not trades:
                return 0.0
                
            profitable_trades = sum(1 for trade in trades if trade.get('profit_zar', 0) > 0)
            return profitable_trades / len(trades)
            
        except Exception as e:
            logger.error(f"Win rate calculation failed: {e}")
            return 0.0
            
    def calculate_sharpe_ratio(self, trades: List[Dict], risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(trades) < 2:
                return 0.0
                
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            daily_pnl = df.groupby('date')['profit_zar'].sum().reset_index()
            daily_returns = daily_pnl['profit_zar'].values
            
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            
            if std_return == 0:
                return 0.0
                
            # Annualized Sharpe ratio
            sharpe = (mean_return * 252 - risk_free_rate) / (std_return * np.sqrt(252))
            return sharpe
            
        except Exception as e:
            logger.error(f"Sharpe ratio calculation failed: {e}")
            return 0.0
            
    def calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        try:
            if not trades:
                return 0.0
                
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate cumulative P&L
            df['cumulative_pnl'] = df['profit_zar'].cumsum()
            
            # Calculate running maximum
            df['running_max'] = df['cumulative_pnl'].expanding().max()
            
            # Calculate drawdown
            df['drawdown'] = df['cumulative_pnl'] - df['running_max']
            
            max_drawdown = df['drawdown'].min()
            return abs(max_drawdown)
            
        except Exception as e:
            logger.error(f"Max drawdown calculation failed: {e}")
            return 0.0
            
    def get_confidence_level(self, trades: List[Dict]) -> Dict[str, Any]:
        """Get overall confidence assessment"""
        try:
            if not trades:
                return {"level": "none", "score": 0.0, "message": "No trading data available"}
                
            # Calculate various confidence metrics
            data_quality = min(len(trades) / 100, 1.0)  # Based on number of trades
            
            # Time span coverage
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            time_span_days = (df['timestamp'].max() - df['timestamp'].min()).days
            time_coverage = min(time_span_days / 30, 1.0)  # Based on days of data
            
            # Performance consistency
            win_rate = self.calculate_win_rate(trades)
            consistency = 1.0 - abs(win_rate - 0.5) * 2  # Closer to 50% is more consistent
            
            # Overall confidence
            confidence_score = (data_quality + time_coverage + consistency) / 3
            
            level_map = {
                (0.8, 1.0): "very_high",
                (0.6, 0.8): "high", 
                (0.4, 0.6): "medium",
                (0.2, 0.4): "low",
                (0.0, 0.2): "very_low"
            }
            
            confidence_level = "unknown"
            for (min_val, max_val), level in level_map.items():
                if min_val <= confidence_score < max_val:
                    confidence_level = level
                    break
                    
            return {
                "level": confidence_level,
                "score": round(confidence_score, 3),
                "metrics": {
                    "data_quality": round(data_quality, 3),
                    "time_coverage": round(time_coverage, 3),
                    "consistency": round(consistency, 3),
                    "total_trades": len(trades),
                    "time_span_days": time_span_days,
                    "win_rate": round(win_rate, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Confidence level calculation failed: {e}")
            return {"level": "error", "score": 0.0, "message": str(e)}