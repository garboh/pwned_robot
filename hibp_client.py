"""
HaveIBeenPwned API client with caching, retry logic, and rate limiting.
"""

import logging
import hashlib
from typing import Optional
from datetime import datetime, timezone, timedelta
import asyncio

import aiohttp
from aiohttp import ClientSession, ClientError, ClientConnectorError
import redis
import redis.asyncio as aioredis

from config import settings
from security import AuditLogger, InputValidator

logger = logging.getLogger(__name__)


class HibpClient:
    """
    Async client for HaveIBeenPwned API v3.
    Includes caching, retry logic, and rate limiting.
    """
    
    def __init__(self, api_key: str, base_url: str = settings.HIBP_API_BASE_URL):
        """
        Initialize HIBP client.
        
        Args:
            api_key: HaveIBeenPwned API key
            base_url: Base URL for HIBP API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = settings.HIBP_API_TIMEOUT
        self.session: Optional[ClientSession] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.headers = {
            "User-Agent": "pwned_robot/2.0 (Security Check Bot)",
            "Accept": "application/json",
        }
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session and Redis connection."""
        self.session = ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        
        try:
            self.redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed, running without cache: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close HTTP session and Redis connection."""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def _get_from_cache(self, key: str) -> Optional[str]:
        """Retrieve value from Redis cache."""
        if not self.redis_client or not settings.ENABLE_CACHE:
            return None
        
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def _set_cache(self, key: str, value: str, ttl: int = settings.CACHE_EXPIRATION):
        """Store value in Redis cache."""
        if not self.redis_client or not settings.ENABLE_CACHE:
            return
        
        try:
            await self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def _get_cache_key(self, email: str, endpoint: str) -> str:
        """Generate cache key for email."""
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        return f"hibp:{endpoint}:{email_hash}"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        """
        Make HTTP request to HIBP API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for request
            
        Returns:
            JSON response
            
        Raises:
            HibpApiError: If API request fails
        """
        if not self.session:
            raise RuntimeError("Client not connected. Use 'async with' or call connect()")
        
        url = f"{self.base_url}/{endpoint}"
        headers = {**self.headers, "user-agent": self.headers["User-Agent"]}
        
        if self.api_key:
            headers["user-agent"] = f"{headers['user-agent']}:{self.api_key}"
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                ) as response:
                    
                    # Handle rate limiting (429)
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                        logger.warning(f"Rate limited. Waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Success
                    if response.status == 200:
                        return await response.json()
                    
                    # Not found (no breaches)
                    if response.status == 404:
                        return None
                    
                    # Bad request or other errors
                    if response.status >= 400:
                        error_data = await response.text()
                        raise HibpApiError(
                            f"API error {response.status}: {error_data}"
                        )
                    
                    # Other successful status codes
                    return await response.json()
                    
            except (ClientConnectorError, asyncio.TimeoutError) as e:
                last_error = e
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
        
        raise HibpApiError(f"API request failed after {self.max_retries} attempts: {last_error}")
    
    async def check_breaches(self, email: str, include_unverified: bool = False) -> dict:
        """
        Check if email appears in any known breaches.
        
        Args:
            email: Email to check
            include_unverified: Include unverified breaches
            
        Returns:
            Dictionary with breach information
        """
        # Validate email
        is_valid, sanitized_email = InputValidator.validate_email(email)
        if not is_valid:
            raise ValueError(f"Invalid email format: {email}")
        
        email = sanitized_email
        
        # Check cache
        cache_key = self._get_cache_key(email, "breaches")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for breaches: {email}")
            return {"from_cache": True, "data": cached_result}
        
        try:
            # Make API request
            endpoint = f"breachedaccount/{email.lower()}"
            params = {}
            if include_unverified:
                params["includeUnverified"] = "true"
            
            breaches = await self._make_request("GET", endpoint, params=params)
            
            # Log the check
            AuditLogger.log_breach_check(
                user_id=None,
                email=email,
                success=True
            )
            
            # Cache result
            import json
            if breaches:
                await self._set_cache(cache_key, json.dumps(breaches))
            
            return {"from_cache": False, "data": breaches or []}
            
        except Exception as e:
            logger.error(f"Breach check failed for {email}: {e}")
            AuditLogger.log_breach_check(
                user_id=None,
                email=email,
                success=False,
                error=str(e)
            )
            raise
    
    async def check_pastes(self, email: str) -> list:
        """
        Check if email appears in any known pastes.
        
        Args:
            email: Email to check
            
        Returns:
            List of pastes
        """
        # Validate email
        is_valid, sanitized_email = InputValidator.validate_email(email)
        if not is_valid:
            raise ValueError(f"Invalid email format: {email}")
        
        email = sanitized_email
        
        # Check cache
        cache_key = self._get_cache_key(email, "pastes")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for pastes: {email}")
            return {"from_cache": True, "data": cached_result}
        
        try:
            endpoint = f"pasteaccount/{email.lower()}"
            pastes = await self._make_request("GET", endpoint)
            
            # Cache result
            import json
            if pastes:
                await self._set_cache(cache_key, json.dumps(pastes))
            
            return {"from_cache": False, "data": pastes or []}
            
        except Exception as e:
            logger.error(f"Paste check failed for {email}: {e}")
            raise
    
    async def get_breach_details(self, breach_name: str) -> dict:
        """
        Get detailed information about a specific breach.
        
        Args:
            breach_name: Name of the breach
            
        Returns:
            Breach details
        """
        # Sanitize breach name to prevent injection
        breach_name = InputValidator.sanitize_string(breach_name, max_length=100)
        
        try:
            endpoint = f"breach/{breach_name}"
            return await self._make_request("GET", endpoint)
        except Exception as e:
            logger.error(f"Failed to get breach details for {breach_name}: {e}")
            raise


class HibpApiError(Exception):
    """Raised when HIBP API request fails."""
    pass
