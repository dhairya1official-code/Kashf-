"""
Kashf Backend — Database Layer
Async SQLAlchemy with SQLite for scan tasks, findings, and threat reports.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings

# ── Async Engine & Session ────────────────────────────────────────────
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Models ────────────────────────────────────────────────────────────


class ScanTask(Base):
    """Represents a single OSINT scan job."""

    __tablename__ = "scan_tasks"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    query = Column(String(255), nullable=False, index=True)
    query_type = Column(String(20), nullable=False)  # "email" | "username"
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)  # 0–100%
    created_at = Column(DateTime, default=_utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    findings = relationship("Finding", back_populates="task", cascade="all, delete-orphan")
    threat_report = relationship(
        "ThreatReport", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ScanTask {self.id[:8]}… query={self.query!r} status={self.status}>"


class Finding(Base):
    """A single discovery from a scraper — one per platform hit."""

    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    task_id = Column(String(36), ForeignKey("scan_tasks.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    url = Column(String(500), nullable=True)
    found = Column(Integer, default=0)  # 1 = found, 0 = not found
    data_found = Column(Text, nullable=True)  # JSON string of extracted data
    risk_category = Column(String(50), nullable=True)
    risk_score = Column(Float, default=0.0)  # 0.0–10.0
    checked_at = Column(DateTime, default=_utc_now)

    # Relationships
    task = relationship("ScanTask", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding {self.platform} found={self.found} score={self.risk_score}>"


class ThreatReport(Base):
    """Aggregated threat analysis for a completed scan."""

    __tablename__ = "threat_reports"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    task_id = Column(String(36), ForeignKey("scan_tasks.id"), nullable=False, unique=True)
    overall_score = Column(Float, default=0.0)  # 0.0–100.0
    risk_level = Column(String(20), default="low")  # low / medium / high / critical
    summary = Column(Text, nullable=True)  # JSON string
    recommendations = Column(Text, nullable=True)  # JSON string
    category_scores = Column(Text, nullable=True)  # JSON string — per-category breakdown
    generated_at = Column(DateTime, default=_utc_now)

    # Relationships
    task = relationship("ScanTask", back_populates="threat_report")

    def __repr__(self) -> str:
        return f"<ThreatReport task={self.task_id[:8]}… score={self.overall_score}>"


# ── Helpers ───────────────────────────────────────────────────────────


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency-injectable async session generator."""
    async with AsyncSessionLocal() as session:
        yield session
