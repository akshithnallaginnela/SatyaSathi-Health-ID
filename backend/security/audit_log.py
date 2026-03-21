"""
Audit logging — records all significant user actions for security.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import AsyncSession
from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_id = Column(String(100), nullable=True)
    success = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


async def log_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    metadata: Optional[dict] = None,
):
    """Log a security/audit event."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        success=success,
        metadata_json=metadata,
    )
    db.add(log)
    # Note: commit is handled by the session dependency
