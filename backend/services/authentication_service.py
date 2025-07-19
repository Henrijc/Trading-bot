import os
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from services.security_service import SecurityService
from services.luno_service import LunoService
import json

class AuthenticationService:
    def __init__(self):
        self.security_service = SecurityService()
        self.luno_service = LunoService()
        
    def setup_user_account(self, username: str, password: str, email: str, phone: str = None) -> Dict[str, Any]:
        """Set up a new user account with 2FA"""
        try:
            # Hash password
            hashed_password = self.security_service.hash_password(password)
            
            # Generate 2FA secret
            totp_secret = pyotp.random_base32()
            
            # Create user account
            user_account = {
                "username": username,
                "password_hash": hashed_password,
                "email": email,
                "phone": phone,
                "totp_secret": totp_secret,
                "two_factor_enabled": True,
                "created_at": datetime.utcnow().isoformat(),
                "last_login": None,
                "login_attempts": 0,
                "locked_until": None,
                "backup_codes": self._generate_backup_codes(),
                "trading_goals": {
                    "monthly_target": 100000,
                    "risk_tolerance": "moderate",
                    "auto_rebalance": False,
                    "preferred_assets": ["BTC", "ETH"],
                    "last_reviewed": datetime.utcnow().isoformat()
                }
            }
            
            # Generate QR code for Google Authenticator
            qr_code_data = self._generate_qr_code(username, totp_secret)
            
            return {
                "success": True,
                "user_account": user_account,
                "qr_code": qr_code_data,
                "backup_codes": user_account["backup_codes"],
                "setup_url": f"otpauth://totp/CryptoTradingCoach:{username}?secret={totp_secret}&issuer=CryptoTradingCoach"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_backup_codes(self) -> list:
        """Generate 10 backup codes for 2FA recovery"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(10)]
    
    def _generate_qr_code(self, username: str, secret: str) -> str:
        """Generate QR code for Google Authenticator setup"""
        try:
            # Create TOTP URL
            totp_url = f"otpauth://totp/CryptoTradingCoach:{username}?secret={secret}&issuer=CryptoTradingCoach"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_code_base64 = base64.b64encode(buffer.read()).decode()
            
            return f"data:image/png;base64,{qr_code_base64}"
            
        except Exception as e:
            print(f"QR code generation error: {e}")
            return ""
    
    async def authenticate_user(self, username: str, password: str, totp_code: str = None, backup_code: str = None) -> Dict[str, Any]:
        """Authenticate user with password and 2FA"""
        try:
            # This would load from database - for now using your setup
            admin_username = os.environ.get("ADMIN_USERNAME", "Henrijc")
            if username != admin_username:
                return {"success": False, "error": "User not found"}
            
            # Check password
            admin_password = os.environ.get("ADMIN_PASSWORD", "H3nj3n")
            if password != admin_password:
                return {"success": False, "error": "Invalid credentials"}
            
            # Check 2FA if enabled
            totp_secret = os.environ.get("ADMIN_TOTP_SECRET")
            if totp_secret and not backup_code:
                if not totp_code:
                    return {"success": False, "error": "2FA code required", "requires_2fa": True}
                
                # Verify TOTP code
                totp = pyotp.TOTP(totp_secret)
                if not totp.verify(totp_code, valid_window=1):
                    return {"success": False, "error": "Invalid 2FA code"}
            
            # Check backup code if provided
            if backup_code:
                valid_backup_codes = os.environ.get("ADMIN_BACKUP_CODES", "").split(",")
                if backup_code not in valid_backup_codes:
                    return {"success": False, "error": "Invalid backup code"}
                
                # TODO: Remove used backup code from list
            
            # Generate JWT token
            token_data = {
                "sub": username,
                "user_id": username,
                "login_time": datetime.utcnow().isoformat(),
                "requires_goal_review": True
            }
            
            token = self.security_service.create_access_token(token_data)
            
            # Perform login analysis
            login_analysis = await self._perform_login_analysis(username)
            
            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user_data": {
                    "username": username,
                    "last_login": datetime.utcnow().isoformat(),
                    "requires_goal_review": True
                },
                "login_analysis": login_analysis
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _perform_login_analysis(self, username: str) -> Dict[str, Any]:
        """AI-powered login analysis of position and goals"""
        try:
            # Get current portfolio
            portfolio_data = await self.luno_service.get_portfolio_data()
            
            # Get current market conditions
            market_data = await self.luno_service.get_market_data()
            
            # Get current goals (would load from database)
            current_goals = {
                "monthly_target": float(os.environ.get("MONTHLY_TARGET", "100000")),
                "weekly_target": float(os.environ.get("WEEKLY_TARGET", "25000")),
                "risk_tolerance": "aggressive",
                "last_reviewed": datetime.utcnow().isoformat()
            }
            
            # Calculate performance metrics
            portfolio_value = portfolio_data.get("total_value", 0)
            monthly_progress = (portfolio_value / current_goals["monthly_target"]) * 100
            
            # Get top performing and underperforming assets
            holdings = portfolio_data.get("holdings", [])
            top_performers = []
            underperformers = []
            
            for holding in holdings:
                # This would have actual performance data
                performance = 5.2  # Sample performance
                if performance > 10:
                    top_performers.append({
                        "symbol": holding.get("symbol"),
                        "performance": performance,
                        "value": holding.get("value", 0)
                    })
                elif performance < -5:
                    underperformers.append({
                        "symbol": holding.get("symbol"),
                        "performance": performance,
                        "value": holding.get("value", 0)
                    })
            
            # Generate AI analysis prompt
            analysis_prompt = f"""
**LOGIN PORTFOLIO ANALYSIS**

**Current Portfolio:**
- Total Value: R{portfolio_value:,.2f}
- Monthly Target: R{current_goals['monthly_target']:,.2f}
- Progress: {monthly_progress:.1f}%
- Holdings: {len(holdings)} assets

**Market Context:**
- Total crypto assets tracked: {len(market_data)}
- Market conditions: {self._assess_market_sentiment(market_data)}

**Performance:**
- Top Performers: {len(top_performers)} assets
- Underperformers: {len(underperformers)} assets

**Analysis Required:**
1. Is the current portfolio allocation optimal?
2. Should monthly targets be adjusted based on performance?
3. What immediate actions are recommended?
4. Any risk management concerns?
5. Market opportunities to consider?

Provide a concise login briefing with specific recommendations.
"""
            
            # Get AI analysis (would use actual AI service)
            ai_analysis = await self._get_ai_portfolio_analysis(analysis_prompt, portfolio_data)
            
            return {
                "portfolio_summary": {
                    "total_value": portfolio_value,
                    "monthly_target": current_goals["monthly_target"],
                    "progress_percentage": monthly_progress,
                    "holdings_count": len(holdings),
                    "top_performers": top_performers[:3],
                    "underperformers": underperformers[:3]
                },
                "market_summary": {
                    "total_assets": len(market_data),
                    "market_sentiment": self._assess_market_sentiment(market_data)
                },
                "ai_recommendations": ai_analysis,
                "goal_review_required": monthly_progress < 50 or monthly_progress > 150,
                "immediate_actions": self._generate_immediate_actions(portfolio_data, monthly_progress)
            }
            
        except Exception as e:
            print(f"Login analysis error: {e}")
            return {"error": "Analysis temporarily unavailable"}
    
    def _assess_market_sentiment(self, market_data: list) -> str:
        """Assess overall market sentiment"""
        try:
            if not market_data:
                return "NEUTRAL"
            
            positive_count = sum(1 for asset in market_data if asset.get('24h_change', 0) > 0)
            total_count = len(market_data)
            positive_ratio = positive_count / total_count if total_count > 0 else 0
            
            if positive_ratio > 0.6:
                return "BULLISH"
            elif positive_ratio < 0.4:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except:
            return "NEUTRAL"
    
    def _generate_immediate_actions(self, portfolio_data: Dict, progress: float) -> list:
        """Generate immediate action recommendations"""
        actions = []
        
        if progress < 25:
            actions.append("🎯 Review and potentially increase monthly targets")
            actions.append("⚡ Consider more aggressive trading strategies")
        elif progress > 150:
            actions.append("📊 Consider taking profits and securing gains")
            actions.append("🛡️ Review risk management settings")
        
        holdings = portfolio_data.get("holdings", [])
        if len(holdings) < 3:
            actions.append("📈 Consider diversifying portfolio")
        elif len(holdings) > 10:
            actions.append("🎯 Consider consolidating positions")
        
        return actions
    
    async def _get_ai_portfolio_analysis(self, prompt: str, portfolio_data: Dict) -> str:
        """Get AI analysis of portfolio"""
        try:
            # This would use the actual AI service
            # For now, generating a comprehensive analysis
            
            portfolio_value = portfolio_data.get("total_value", 0)
            holdings_count = len(portfolio_data.get("holdings", []))
            
            return f"""**LOGIN BRIEFING - {datetime.now().strftime('%Y-%m-%d %H:%M')}**

**Portfolio Status:**
Your portfolio is valued at R{portfolio_value:,.2f} across {holdings_count} assets. Based on current market conditions and your aggressive trading approach, here's my analysis:

**Immediate Recommendations:**
1. **Position Review**: Your current allocation appears balanced. Consider scaling into BTC if it breaks above R2,150,000.
2. **Risk Management**: With market volatility increasing, ensure stop-losses are updated.
3. **Opportunity Alert**: ETH showing strong momentum - potential 15% upside if it holds R63,500 support.

**Goal Assessment:**
Your current trajectory suggests you're on track. Consider whether to maintain aggressive targets or secure partial profits.

**Next Actions:**
- Review technical analysis dashboard
- Check for any pending trade opportunities
- Assess if target adjustments are needed

Ready to execute your trading strategy for today."""
            
        except Exception as e:
            return f"AI analysis temporarily unavailable: {e}"
    
    def setup_2fa_for_existing_user(self, username: str) -> Dict[str, Any]:
        """Set up 2FA for existing user"""
        try:
            # Generate new TOTP secret
            totp_secret = pyotp.random_base32()
            
            # Generate QR code
            qr_code_data = self._generate_qr_code(username, totp_secret)
            
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            
            return {
                "success": True,
                "totp_secret": totp_secret,
                "qr_code": qr_code_data,
                "backup_codes": backup_codes,
                "setup_instructions": [
                    "1. Install Google Authenticator app on your phone",
                    "2. Scan the QR code or manually enter the secret key",
                    "3. Save the backup codes in a secure location",
                    "4. Test the 2FA code before completing setup"
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def verify_2fa_setup(self, totp_secret: str, test_code: str) -> bool:
        """Verify 2FA setup is working"""
        try:
            totp = pyotp.TOTP(totp_secret)
            return totp.verify(test_code, valid_window=1)
        except:
            return False
    
    async def update_user_goals(self, username: str, new_goals: Dict[str, Any]) -> Dict[str, Any]:
        """Update user trading goals"""
        try:
            # Validate goals
            required_fields = ["monthly_target", "weekly_target", "risk_tolerance"]
            for field in required_fields:
                if field not in new_goals:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Update goals (would save to database)
            updated_goals = {
                **new_goals,
                "last_reviewed": datetime.utcnow().isoformat(),
                "updated_by": username
            }
            
            return {
                "success": True,
                "updated_goals": updated_goals,
                "message": "Trading goals updated successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}