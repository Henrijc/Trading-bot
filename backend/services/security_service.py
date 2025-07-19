import os
import hashlib
import hmac
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import bcrypt

class SecurityService:
    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY', self._generate_secret())
        self.algorithm = "HS256"
        self.token_expire_minutes = 30
        
    def _generate_secret(self) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(64)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def encrypt_sensitive_data(self, data: str, user_key: str) -> str:
        """Encrypt sensitive data like API keys"""
        import base64
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Generate key from user key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_for_encryption',  # In production, use random salt per user
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(user_key.encode()))
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, user_key: str) -> str:
        """Decrypt sensitive data"""
        import base64
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        try:
            # Generate same key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'salt_for_encryption',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(user_key.encode()))
            fernet = Fernet(key)
            
            # Decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""
    
    def validate_api_request(self, request_data: Dict[str, Any], user_id: str) -> bool:
        """Validate API request for security"""
        
        # Check request size limits
        if len(str(request_data)) > 50000:  # 50KB limit
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script>', 'javascript:', 'eval(', 'exec(', '; DROP', 'UNION SELECT']
        request_str = str(request_data).lower()
        
        for pattern in suspicious_patterns:
            if pattern.lower() in request_str:
                return False
        
        return True
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security events"""
        security_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "ip_address": details.get("ip_address", "unknown")
        }
        
        # In production, this would write to secure log file or security monitoring system
        print(f"🛡️ SECURITY EVENT: {security_log}")
    
    def rate_limit_check(self, user_id: str, action: str, max_requests: int = 100, time_window_minutes: int = 60) -> bool:
        """Check rate limiting"""
        # In production, this would use Redis or similar for distributed rate limiting
        # For now, basic implementation
        return True  # Placeholder
    
    def validate_trading_request(self, trade_data: Dict[str, Any], user_portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trading requests for security"""
        validation_result = {"valid": True, "errors": []}
        
        # Check trade amount limits
        trade_amount = trade_data.get("amount", 0)
        portfolio_value = user_portfolio.get("total_value", 0)
        
        if trade_amount > portfolio_value * 0.5:  # Max 50% of portfolio per trade
            validation_result["valid"] = False
            validation_result["errors"].append("Trade amount exceeds 50% of portfolio")
        
        if trade_amount < 100:  # Minimum trade amount R100
            validation_result["valid"] = False
            validation_result["errors"].append("Trade amount below minimum R100")
        
        # Validate symbol
        allowed_symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOT', 'MATIC', 'LTC']
        if trade_data.get("symbol") not in allowed_symbols:
            validation_result["valid"] = False
            validation_result["errors"].append("Invalid trading symbol")
        
        return validation_result
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize user input"""
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            import re
            sanitized = re.sub(r'[<>"\'\(\);]', '', input_data)
            return sanitized.strip()[:1000]  # Limit length
        elif isinstance(input_data, dict):
            return {self.sanitize_input(k): self.sanitize_input(v) for k, v in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data