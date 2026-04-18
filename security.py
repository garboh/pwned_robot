"""
Security utilities for pwned_robot.
Handles input validation, rate limiting, encryption, and audit logging.
"""

import hashlib
import re
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from functools import wraps
import asyncio

from cryptography.fernet import Fernet
import bleach
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validates and sanitizes user input to prevent injection attacks.
    """
    
    # Email regex (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )
    
    # Dangerous characters that could indicate injection attempts
    DANGEROUS_CHARS = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, Optional[str]]:
        """
        Validate email format and length.
        
        Returns:
            Tuple of (is_valid, sanitized_email)
        """
        if not email or len(email) > 254:
            return False, None
        
        email = email.strip().lower()
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            return False, None
        
        return True, email
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input to prevent XSS and injection attacks.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return ""
        
        # Limit length
        text = text[:max_length]
        
        # Remove HTML/XML tags
        text = bleach.clean(text, tags=[], strip=True)
        
        # Remove control characters
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")
        
        return text.strip()
    
    @staticmethod
    def check_injection_attempts(text: str) -> bool:
        """
        Check for potential SQL injection or command injection attempts.
        
        Returns:
            True if potentially dangerous, False otherwise
        """
        text_lower = text.lower()
        
        for dangerous in InputValidator.DANGEROUS_CHARS:
            if dangerous.lower() in text_lower:
                return True
        
        # Check for common injection patterns
        patterns = [
            r"union\s+select",
            r"select\s+.*\s+from",
            r"insert\s+into",
            r"delete\s+from",
            r"drop\s+table",
            r"exec\s*\(",
            r"<script",
            r"javascript:",
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False


class EncryptionManager:
    """
    Handles encryption/decryption of sensitive data.
    Uses Fernet (AES-128) for symmetric encryption.
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            key: Encryption key (if None, generates a new one)
        """
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, data: str) -> str:
        """Decrypt encrypted data."""
        try:
            decrypted = self.cipher.decrypt(data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")


class PasswordHasher:
    """
    Handles secure password hashing using SHA-256 with salt.
    Note: For actual password storage, use bcrypt or Argon2.
    This is for demonstrative purposes.
    """
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash password with salt.
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if not salt:
            salt = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:32]
        
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash."""
        new_hash, _ = PasswordHasher.hash_password(password, salt)
        return new_hash == hashed


class RateLimiter:
    """
    Rate limiting to prevent abuse and DoS attacks.
    """
    
    def __init__(self, calls: int = 5, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
    
    @sleep_and_retry
    @limits(calls=5, period=60)
    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded."""
        return True
    
    async def check_rate_limit_async(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        Check rate limit for user (async version).
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # This would typically check against Redis or database
        # For now, returning True
        return True, None


class AuditLogger:
    """
    Logs security-relevant events for audit trails.
    """
    
    @staticmethod
    def log_breach_check(user_id: int, email: str, success: bool, error: Optional[str] = None):
        """Log a breach check attempt."""
        logger.info(
            f"Breach check | User: {user_id} | Email: {email} | Success: {success}",
            extra={
                "user_id": user_id,
                "action": "breach_check",
                "email_hash": hashlib.sha256(email.encode()).hexdigest()[:16],
                "success": success,
                "error": error,
            }
        )
    
    @staticmethod
    def log_security_event(user_id: Optional[int], event_type: str, details: str):
        """Log security-relevant event."""
        logger.warning(
            f"Security event: {event_type} | Details: {details}",
            extra={
                "user_id": user_id,
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    @staticmethod
    def log_suspicious_activity(user_id: int, activity: str, severity: str = "medium"):
        """Log suspicious user activity."""
        logger.warning(
            f"Suspicious activity | User: {user_id} | Activity: {activity} | Severity: {severity}",
            extra={
                "user_id": user_id,
                "activity": activity,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


def require_admin(func):
    """
    Decorator to require admin privileges for a command handler.
    Works for both plain functions (update, context) and bound methods (self, update, context).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from config import settings

        # args = (update, context) or (self, update, context)
        update = args[1] if (args and hasattr(args[0], '__class__')
                             and not hasattr(args[0], 'effective_user')) else args[0]

        if update.effective_user.id not in settings.TELEGRAM_ADMIN_IDS:
            await update.message.reply_text(
                "❌ Non hai i permessi per usare questo comando."
            )
            return

        return await func(*args, **kwargs)

    return wrapper


def handle_errors(func):
    """
    Decorator to handle errors gracefully in handlers.
    Works for both plain functions (update, context) and bound methods (self, update, context).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # args = (update, context) or (self, update, context)
        update = args[1] if (args and hasattr(args[0], '__class__')
                             and not hasattr(args[0], 'effective_user')) else args[0]
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "❌ Si è verificato un errore. Per favore riprova più tardi."
                )
            except:
                pass
    
    return wrapper
