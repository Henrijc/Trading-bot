"""
TargetService - Manages user trading targets and performance goals
This service handles CRUD operations for user targets and goal management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

class TargetService:
    """
    Service to manage user trading targets and performance goals
    """
    
    def __init__(self, db_client=None):
        if db_client:
            self.db = db_client[os.environ.get('DB_NAME', 'crypto_trading')]
        else:
            # Fallback to create own connection if needed
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = AsyncIOMotorClient(mongo_url)
            self.db = client[os.environ.get('DB_NAME', 'crypto_trading')]
        
        logger.info("TargetService initialized")
    
    async def get_user_targets(self, user_id: str = "default_user") -> Dict:
        """Get current targets for a user"""
        try:
            targets = await self.db.target_settings.find_one({"user_id": user_id})
            
            # Define required fields with defaults based on user requirements
            required_defaults = {
                "user_id": user_id,
                "monthly_target": 8000,  # User's goal: R8000/month
                "weekly_target": 2000,   # R8000/4 weeks
                "daily_target": 267,     # R8000/30 days
                "current_capital": 154273.71,  # User's current capital
                "risk_per_trade": 0.04,  # 4% risk management
                "xrp_reserve": 1000,     # Keep 1000 XRP long-term
                "auto_adjust": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if not targets:
                # Create default targets
                await self.db.target_settings.insert_one(required_defaults)
                targets = required_defaults
            else:
                # Ensure existing targets have all required fields
                needs_update = False
                for key, default_value in required_defaults.items():
                    if key not in targets:
                        targets[key] = default_value
                        needs_update = True
                
                # Update database if we added missing fields
                if needs_update:
                    targets["updated_at"] = datetime.utcnow().isoformat()
                    await self.db.target_settings.update_one(
                        {"user_id": user_id},
                        {"$set": targets}
                    )
            
            # Remove MongoDB ObjectId
            if '_id' in targets:
                del targets['_id']
            
            return targets
            
        except Exception as e:
            logger.error(f"Error getting user targets: {e}")
            raise
    
    async def update_user_targets(self, user_id: str, targets: Dict) -> Dict:
        """Update user targets"""
        try:
            targets["user_id"] = user_id
            targets["updated_at"] = datetime.utcnow().isoformat()
            
            # Validate target values
            if "monthly_target" in targets and targets["monthly_target"] <= 0:
                raise ValueError("Monthly target must be positive")
            
            if "risk_per_trade" in targets:
                if not (0 < targets["risk_per_trade"] <= 1):
                    raise ValueError("Risk per trade must be between 0 and 1")
            
            await self.db.target_settings.update_one(
                {"user_id": user_id},
                {"$set": targets},
                upsert=True
            )
            
            # Return updated targets
            return await self.get_user_targets(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user targets: {e}")
            raise
    
    async def calculate_progress(self, user_id: str = "default_user") -> Dict:
        """Calculate progress towards targets"""
        try:
            targets = await self.get_user_targets(user_id)
            
            # Get current date range
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=now.weekday())
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get performance data from trades/profit
            monthly_profit = await self._get_profit_for_period(user_id, month_start, now)
            weekly_profit = await self._get_profit_for_period(user_id, week_start, now)
            daily_profit = await self._get_profit_for_period(user_id, day_start, now)
            
            # Calculate progress percentages
            monthly_progress = (monthly_profit / targets["monthly_target"]) * 100 if targets["monthly_target"] > 0 else 0
            weekly_progress = (weekly_profit / targets["weekly_target"]) * 100 if targets["weekly_target"] > 0 else 0
            daily_progress = (daily_profit / targets["daily_target"]) * 100 if targets["daily_target"] > 0 else 0
            
            return {
                "user_id": user_id,
                "targets": targets,
                "current_performance": {
                    "monthly_profit": monthly_profit,
                    "weekly_profit": weekly_profit,
                    "daily_profit": daily_profit
                },
                "progress": {
                    "monthly_progress": monthly_progress,
                    "weekly_progress": weekly_progress,
                    "daily_progress": daily_progress
                },
                "remaining": {
                    "monthly_remaining": max(0, targets["monthly_target"] - monthly_profit),
                    "weekly_remaining": max(0, targets["weekly_target"] - weekly_profit),
                    "daily_remaining": max(0, targets["daily_target"] - daily_profit)
                },
                "status": {
                    "monthly_on_track": monthly_progress >= 80,
                    "weekly_on_track": weekly_progress >= 80,
                    "daily_on_track": daily_progress >= 80
                },
                "calculated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            raise
    
    async def _get_profit_for_period(self, user_id: str, start_date: datetime, end_date: datetime) -> float:
        """Get total profit for a specific time period"""
        try:
            # Query closed trades within the period
            trades = await self.db.trades.find({
                "user_id": user_id,
                "status": "closed",
                "exit_time": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }).to_list(None)
            
            total_profit = 0.0
            for trade in trades:
                if trade.get("profit_zar"):
                    total_profit += trade["profit_zar"]
                elif trade.get("exit_rate") and trade.get("entry_rate") and trade.get("amount"):
                    # Calculate profit if not stored
                    profit = trade["amount"] * (trade["exit_rate"] - trade["entry_rate"])
                    total_profit += profit
            
            return total_profit
            
        except Exception as e:
            logger.error(f"Error getting profit for period: {e}")
            return 0.0
    
    async def adjust_targets_based_on_performance(self, user_id: str = "default_user") -> Dict:
        """Auto-adjust targets based on recent performance"""
        try:
            progress = await self.calculate_progress(user_id)
            targets = progress["targets"]
            
            # Only auto-adjust if enabled
            if not targets.get("auto_adjust", False):
                return {"adjusted": False, "reason": "Auto-adjust disabled"}
            
            current_performance = progress["current_performance"]
            monthly_progress = progress["progress"]["monthly_progress"]
            
            # Adjustment logic
            adjustments = {}
            
            # If consistently underperforming (< 50% monthly target)
            if monthly_progress < 50:
                # Reduce targets by 20%
                adjustments["monthly_target"] = targets["monthly_target"] * 0.8
                adjustments["weekly_target"] = targets["weekly_target"] * 0.8
                adjustments["daily_target"] = targets["daily_target"] * 0.8
                reason = "Reduced targets due to underperformance"
            
            # If consistently overperforming (> 150% monthly target)
            elif monthly_progress > 150:
                # Increase targets by 20%
                adjustments["monthly_target"] = targets["monthly_target"] * 1.2
                adjustments["weekly_target"] = targets["weekly_target"] * 1.2
                adjustments["daily_target"] = targets["daily_target"] * 1.2
                reason = "Increased targets due to strong performance"
            
            else:
                return {"adjusted": False, "reason": "Performance within normal range"}
            
            # Apply adjustments
            if adjustments:
                adjustments["adjustment_date"] = datetime.utcnow().isoformat()
                adjustments["adjustment_reason"] = reason
                
                await self.update_user_targets(user_id, adjustments)
                
                return {
                    "adjusted": True,
                    "reason": reason,
                    "new_targets": adjustments,
                    "previous_monthly": targets["monthly_target"],
                    "new_monthly": adjustments["monthly_target"]
                }
            
            return {"adjusted": False, "reason": "No adjustments needed"}
            
        except Exception as e:
            logger.error(f"Error adjusting targets: {e}")
            raise
    
    async def get_target_history(self, user_id: str = "default_user", days: int = 30) -> List[Dict]:
        """Get history of target changes"""
        try:
            # Get target change history
            history = await self.db.target_history.find(
                {"user_id": user_id}
            ).sort("changed_at", -1).limit(days).to_list(None)
            
            # Remove MongoDB ObjectIds
            for record in history:
                if '_id' in record:
                    del record['_id']
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting target history: {e}")
            return []