import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class SecurityMonitoringService:
    def __init__(self):
        self.security_events = []
        self.alert_thresholds = {
            "failed_logins": 5,
            "large_trades": 50000,  # ZAR
            "api_errors": 10,
            "suspicious_ips": 3
        }
        
    async def monitor_security_events(self):
        """Continuous security monitoring"""
        while True:
            try:
                await self._check_failed_logins()
                await self._check_unusual_trading_patterns()
                await self._check_api_anomalies()
                await self._check_database_integrity()
                
                # Sleep for 5 minutes between checks
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_failed_logins(self):
        """Monitor failed login attempts"""
        try:
            # Check for multiple failed logins from same IP
            recent_failures = await self._get_recent_security_events("FAILED_LOGIN", hours=1)
            
            ip_failures = {}
            for event in recent_failures:
                ip = event.get("details", {}).get("ip_address", "unknown")
                ip_failures[ip] = ip_failures.get(ip, 0) + 1
            
            for ip, count in ip_failures.items():
                if count >= self.alert_thresholds["failed_logins"]:
                    await self._send_security_alert(
                        alert_type="MULTIPLE_FAILED_LOGINS",
                        message=f"IP {ip} has {count} failed login attempts in the last hour",
                        severity="HIGH"
                    )
                    
        except Exception as e:
            print(f"Failed login check error: {e}")
    
    async def _check_unusual_trading_patterns(self):
        """Monitor for unusual trading patterns"""
        try:
            # Check for large trades
            recent_trades = await self._get_recent_trades(hours=24)
            
            for trade in recent_trades:
                amount = trade.get("amount", 0)
                if amount > self.alert_thresholds["large_trades"]:
                    await self._send_security_alert(
                        alert_type="LARGE_TRADE",
                        message=f"Large trade detected: {trade.get('symbol')} for R{amount:,.0f}",
                        severity="MEDIUM"
                    )
            
            # Check for rapid-fire trading
            user_trades = {}
            for trade in recent_trades:
                user_id = trade.get("user_id", "unknown")
                user_trades[user_id] = user_trades.get(user_id, 0) + 1
            
            for user_id, count in user_trades.items():
                if count > 20:  # More than 20 trades in 24h
                    await self._send_security_alert(
                        alert_type="RAPID_TRADING",
                        message=f"User {user_id} executed {count} trades in 24 hours",
                        severity="MEDIUM"
                    )
                    
        except Exception as e:
            print(f"Trading pattern check error: {e}")
    
    async def _check_api_anomalies(self):
        """Monitor API usage for anomalies"""
        try:
            recent_api_calls = await self._get_recent_security_events("API_ACCESS", hours=1)
            
            # Check for rapid API calls from single IP
            ip_calls = {}
            for event in recent_api_calls:
                ip = event.get("details", {}).get("ip_address", "unknown")
                ip_calls[ip] = ip_calls.get(ip, 0) + 1
            
            for ip, count in ip_calls.items():
                if count > 1000:  # More than 1000 calls per hour
                    await self._send_security_alert(
                        alert_type="HIGH_API_USAGE",
                        message=f"IP {ip} made {count} API calls in the last hour",
                        severity="HIGH"
                    )
                    
        except Exception as e:
            print(f"API anomaly check error: {e}")
    
    async def _check_database_integrity(self):
        """Check database for integrity issues"""
        try:
            # Check for data corruption or suspicious modifications
            # This would involve checking checksums, record counts, etc.
            
            # Placeholder for database integrity checks
            integrity_score = await self._calculate_db_integrity_score()
            
            if integrity_score < 0.95:  # Less than 95% integrity
                await self._send_security_alert(
                    alert_type="DATABASE_INTEGRITY",
                    message=f"Database integrity score: {integrity_score:.2%}",
                    severity="HIGH"
                )
                
        except Exception as e:
            print(f"Database integrity check error: {e}")
    
    async def _get_recent_security_events(self, event_type: str, hours: int = 1) -> List[Dict]:
        """Get recent security events from database"""
        # In production, this would query the actual security_events collection
        return []
    
    async def _get_recent_trades(self, hours: int = 24) -> List[Dict]:
        """Get recent trades from database"""
        # In production, this would query the actual trades collection
        return []
    
    async def _calculate_db_integrity_score(self) -> float:
        """Calculate database integrity score"""
        # In production, this would check various integrity metrics
        return 1.0  # Placeholder
    
    async def _send_security_alert(self, alert_type: str, message: str, severity: str):
        """Send security alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        
        print(f"🚨 SECURITY ALERT [{severity}]: {alert_type}")
        print(f"   Message: {message}")
        print(f"   Time: {alert['timestamp']}")
        
        # In production, send email, SMS, or push notifications
        await self._log_security_alert(alert)
        
        if severity == "HIGH":
            await self._send_urgent_notification(alert)
    
    async def _log_security_alert(self, alert: Dict[str, Any]):
        """Log security alert to file and database"""
        try:
            # Write to security log file
            log_entry = f"[{alert['timestamp']}] {alert['severity']}: {alert['alert_type']} - {alert['message']}\n"
            
            with open("/app/backend/logs/security.log", "a") as f:
                f.write(log_entry)
                
            # In production, also store in database for analysis
            
        except Exception as e:
            print(f"Security logging error: {e}")
    
    async def _send_urgent_notification(self, alert: Dict[str, Any]):
        """Send urgent notification for high-severity alerts"""
        try:
            # In production, integrate with email/SMS service
            print(f"📧 URGENT NOTIFICATION SENT: {alert['alert_type']}")
            
        except Exception as e:
            print(f"Urgent notification error: {e}")
    
    def generate_security_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate security report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = {
            "report_period": f"{start_date.date()} to {end_date.date()}",
            "total_security_events": len(self.security_events),
            "event_breakdown": {},
            "threat_level": "LOW",
            "recommendations": []
        }
        
        # Analyze security events
        for event in self.security_events:
            event_type = event.get("alert_type", "unknown")
            report["event_breakdown"][event_type] = report["event_breakdown"].get(event_type, 0) + 1
        
        # Determine threat level
        high_severity_count = sum(1 for e in self.security_events if e.get("severity") == "HIGH")
        if high_severity_count > 5:
            report["threat_level"] = "HIGH"
        elif high_severity_count > 2:
            report["threat_level"] = "MEDIUM"
        
        # Generate recommendations
        if high_severity_count > 0:
            report["recommendations"].append("Review and strengthen authentication mechanisms")
            report["recommendations"].append("Consider implementing additional monitoring")
        
        return report