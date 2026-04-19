"""
Database management module with SQLAlchemy async support.
Handles connection pooling, migrations, and CRUD operations.
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from config import settings
from models import Base, User, BreachCheck, BreachDetail, AuditLog, RateLimitRecord, MonitoredEmail

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations with async support.
    """
    
    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.async_session_maker = None
    
    async def initialize(self):
        """Initialize database engine and session maker."""
        logger.info("Initializing database connection...")
        
        # Create async engine with connection pooling
        engine_kwargs = dict(
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"local_infile": False},
        )
        if settings.DEBUG:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20

        self.engine = create_async_engine(settings.database_url, **engine_kwargs)
        
        # Create session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            future=True,
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def get_session(self) -> AsyncSession:
        """Get new async database session."""
        return self.async_session_maker()
    
    # User operations
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: str = "en"
    ) -> User:
        """Get or create user."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.last_activity = datetime.now(timezone.utc)
                await session.commit()
                return user
            
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )
            session.add(user)
            await session.commit()
            return user
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp."""
        async with self.async_session_maker() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_activity=datetime.now(timezone.utc))
            )
            await session.commit()
    
    # Breach check operations
    
    async def create_breach_check(
        self,
        user_id: int,
        email: str,
        breaches_found: int = 0,
        pastes_found: int = 0,
        check_successful: bool = True,
        error_message: Optional[str] = None
    ) -> BreachCheck:
        """Create new breach check record."""
        async with self.async_session_maker() as session:
            check = BreachCheck(
                user_id=user_id,
                email=email,
                breaches_found=breaches_found,
                pastes_found=pastes_found,
                check_successful=check_successful,
                error_message=error_message,
            )
            session.add(check)
            await session.commit()
            return check
    
    async def get_user_breach_checks(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[BreachCheck]:
        """Get user's breach check history."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(BreachCheck)
                .where(BreachCheck.user_id == user_id)
                .order_by(BreachCheck.checked_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_latest_breach_check(self, user_id: int, email: str) -> Optional[BreachCheck]:
        """Get latest breach check for email."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(BreachCheck)
                .where(
                    and_(
                        BreachCheck.user_id == user_id,
                        BreachCheck.email == email
                    )
                )
                .order_by(BreachCheck.checked_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    # Audit log operations
    
    async def create_audit_log(
        self,
        action: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_details: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry."""
        async with self.async_session_maker() as session:
            log = AuditLog(
                user_id=user_id,
                action=action,
                description=description,
                ip_address=ip_address,
                success=success,
                error_details=error_details,
            )
            session.add(log)
            await session.commit()
            return log
    
    async def get_audit_logs(
        self,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering."""
        async with self.async_session_maker() as session:
            query = select(AuditLog)
            
            if action:
                query = query.where(AuditLog.action == action)
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            
            result = await session.execute(
                query.order_by(AuditLog.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
    
    # Rate limit operations
    
    async def check_rate_limit(
        self,
        user_id: int,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        async with self.async_session_maker() as session:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)
            
            # Count requests in current window
            result = await session.execute(
                select(func.count(RateLimitRecord.id))
                .where(
                    and_(
                        RateLimitRecord.user_id == user_id,
                        RateLimitRecord.endpoint == endpoint,
                        RateLimitRecord.window_start >= window_start
                    )
                )
            )
            count = result.scalar() or 0
            
            is_allowed = count < max_requests
            remaining = max(0, max_requests - count - 1)
            
            return is_allowed, remaining
    
    async def record_request(self, user_id: int, endpoint: str):
        """Record API request for rate limiting."""
        async with self.async_session_maker() as session:
            window_end = datetime.now(timezone.utc) + timedelta(minutes=1)
            
            record = RateLimitRecord(
                user_id=user_id,
                endpoint=endpoint,
                window_end=window_end,
            )
            session.add(record)
            await session.commit()
    
    # Statistics operations
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        async with self.async_session_maker() as session:
            checks_result = await session.execute(
                select(func.count(BreachCheck.id))
                .where(BreachCheck.user_id == user_id)
            )
            total_checks = checks_result.scalar() or 0
            
            breaches_result = await session.execute(
                select(func.sum(BreachCheck.breaches_found))
                .where(BreachCheck.user_id == user_id)
            )
            total_breaches = breaches_result.scalar() or 0
            
            return {
                "total_checks": total_checks,
                "total_breaches": total_breaches,
                "average_breaches": (
                    total_breaches / total_checks if total_checks > 0 else 0
                ),
            }
    
    async def get_global_stats(self) -> dict:
        """Get global statistics."""
        async with self.async_session_maker() as session:
            users_result = await session.execute(select(func.count(User.id)))
            total_users = users_result.scalar() or 0
            
            checks_result = await session.execute(select(func.count(BreachCheck.id)))
            total_checks = checks_result.scalar() or 0
            
            return {
                "total_users": total_users,
                "total_checks": total_checks,
                "average_checks_per_user": (
                    total_checks / total_users if total_users > 0 else 0
                ),
            }

    # Premium operations

    async def update_user_language(self, telegram_id: int, language: str) -> bool:
        """Persist the user's preferred language code."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.language_code = language
            await session.commit()
            return True

    async def set_user_premium(self, telegram_id: int, premium: bool) -> bool:
        """Grant or revoke premium status for a user."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.premium = premium
            user.premium_since = datetime.now(timezone.utc) if premium else None
            await session.commit()
            return True

    # Monitored email operations

    async def add_monitored_email(
        self,
        user_id: int,
        email: str,
        initial_breaches: int = 0,
        initial_pastes: int = 0,
    ) -> Optional[MonitoredEmail]:
        """Add email to monitoring list. Returns None if already monitored."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(MonitoredEmail).where(
                    and_(
                        MonitoredEmail.user_id == user_id,
                        MonitoredEmail.email == email,
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                if not existing.active:
                    existing.active = True
                    existing.last_breaches_count = initial_breaches
                    existing.last_pastes_count = initial_pastes
                    existing.last_checked_at = datetime.now(timezone.utc)
                    await session.commit()
                    return existing
                return None  # Already actively monitored

            monitored = MonitoredEmail(
                user_id=user_id,
                email=email,
                last_breaches_count=initial_breaches,
                last_pastes_count=initial_pastes,
                last_checked_at=datetime.now(timezone.utc),
            )
            session.add(monitored)
            await session.commit()
            return monitored

    async def remove_monitored_email(self, user_id: int, email: str) -> bool:
        """Deactivate email monitoring. Returns True if found and removed."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(MonitoredEmail).where(
                    and_(
                        MonitoredEmail.user_id == user_id,
                        MonitoredEmail.email == email,
                        MonitoredEmail.active == True,
                    )
                )
            )
            monitored = result.scalar_one_or_none()
            if not monitored:
                return False
            monitored.active = False
            await session.commit()
            return True

    async def get_monitored_emails(self, user_id: int) -> List[MonitoredEmail]:
        """Get all active monitored emails for a user."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(MonitoredEmail)
                .where(
                    and_(
                        MonitoredEmail.user_id == user_id,
                        MonitoredEmail.active == True,
                    )
                )
                .order_by(MonitoredEmail.added_at.asc())
            )
            return list(result.scalars().all())

    async def count_monitored_emails(self, user_id: int) -> int:
        """Count active monitored emails for a user."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(func.count(MonitoredEmail.id)).where(
                    and_(
                        MonitoredEmail.user_id == user_id,
                        MonitoredEmail.active == True,
                    )
                )
            )
            return result.scalar() or 0

    async def get_all_premium_monitored_emails(self) -> List[Tuple[MonitoredEmail, User]]:
        """Return all active monitored emails belonging to premium users."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(MonitoredEmail, User)
                .join(User, MonitoredEmail.user_id == User.id)
                .where(
                    and_(
                        MonitoredEmail.active == True,
                        User.premium == True,
                        User.active == True,
                        User.banned == False,
                        User.notifications_enabled == True,
                    )
                )
            )
            return list(result.all())

    async def update_monitored_email_stats(
        self,
        monitored_id: int,
        breaches_count: int,
        pastes_count: int,
    ):
        """Update breach/paste counters after a monitoring check."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(MonitoredEmail).where(MonitoredEmail.id == monitored_id)
            )
            monitored = result.scalar_one_or_none()
            if monitored:
                monitored.last_breaches_count = breaches_count
                monitored.last_pastes_count = pastes_count
                monitored.last_checked_at = datetime.now(timezone.utc)
                await session.commit()


# Global database manager instance
db_manager = DatabaseManager()
