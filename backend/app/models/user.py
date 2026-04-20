"""
User Model — System users with role-based access control (RBAC).
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(Base):
    """Platform user with role-based access control."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), nullable=False, unique=True, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(500), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.ANALYST.value)
    organization = Column(String(300), nullable=True)
    is_active = Column(Integer, default=1)
    is_mfa_enabled = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    cases = relationship("Case", back_populates="owner")

    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"
