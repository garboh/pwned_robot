"""
Database models for pwned_robot using SQLAlchemy ORM.
Includes user profiles, breach records, and audit logs.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """
    User profile model storing user interactions and preferences.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="en")
    
    # User preferences
    notifications_enabled = Column(Boolean, default=True)
    premium = Column(Boolean, default=False)
    premium_since = Column(DateTime, nullable=True)
    
    # Account status
    active = Column(Boolean, default=True)
    banned = Column(Boolean, default=False)
    ban_reason = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime, nullable=True)
    
    # Relationships
    breach_checks = relationship("BreachCheck", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    monitored_emails = relationship("MonitoredEmail", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_telegram_id", "telegram_id"),
        Index("idx_active_users", "active", "banned"),
    )


class BreachCheck(Base):
    """
    Stores information about breach checks performed by users.
    """
    __tablename__ = "breach_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    
    # Results (hashed to prevent plaintext storage)
    breaches_found = Column(Integer, default=0)
    pastes_found = Column(Integer, default=0)
    
    # Status
    check_successful = Column(Boolean, default=True)
    error_message = Column(String(500), nullable=True)
    
    # Timestamps
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    user = relationship("User", back_populates="breach_checks")
    
    __table_args__ = (
        Index("idx_user_email_check", "user_id", "email"),
        Index("idx_checked_at", "checked_at"),
    )


class BreachDetail(Base):
    """
    Detailed information about breaches found for an email.
    """
    __tablename__ = "breach_details"
    
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("breach_checks.id"), nullable=False)
    
    breach_name = Column(String(255), nullable=False)
    breach_title = Column(String(255), nullable=True)
    breach_date = Column(DateTime, nullable=True)
    affected_records = Column(Integer, nullable=True)
    data_classes = Column(Text, nullable=True)  # JSON string
    is_verified = Column(Boolean, default=False)
    is_fabricated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_breach_name", "breach_name"),
    )


class AuditLog(Base):
    """
    Audit trail for security and compliance.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Request details
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    
    # Status
    success = Column(Boolean, default=True)
    error_details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_action", "action"),
        Index("idx_created_at", "created_at"),
        Index("idx_user_action", "user_id", "action"),
    )


class RateLimitRecord(Base):
    """
    Track rate limiting for API calls.
    """
    __tablename__ = "rate_limit_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    endpoint = Column(String(255), nullable=False)
    request_count = Column(Integer, default=1)

    window_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    window_end = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_user_endpoint", "user_id", "endpoint"),
    )


class MonitoredEmail(Base):
    """
    Emails registered by premium users for daily breach monitoring.
    """
    __tablename__ = "monitored_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    # Baseline from last check — used to detect new breaches
    last_breaches_count = Column(Integer, default=0)
    last_pastes_count = Column(Integer, default=0)
    last_checked_at = Column(DateTime, nullable=True)

    active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="monitored_emails")

    __table_args__ = (
        Index("idx_monitored_user_active", "user_id", "active"),
        UniqueConstraint("user_id", "email", name="uq_user_monitored_email"),
    )
