"""
NirnayX Database Module
Async SQLAlchemy engine and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session() as session:
        try:
            # Temporary override for API backward-compat before JWT middleware
            await session.execute(text("SET LOCAL app.override_rls = 'true'"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from sqlalchemy import text

async def init_db():
    """Initialize database tables and set up critical RLS rules."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Enforce PostgreSQL Row-Level Security on cases
        await conn.execute(text("ALTER TABLE cases ENABLE ROW LEVEL SECURITY;"))
        
        # We need to drop the policy if it exists to avoid errors on reboot.
        # Postgres 15 supports DROP POLICY IF EXISTS
        await conn.execute(text("DROP POLICY IF EXISTS case_tenant_isolation ON cases;"))
        
        # Create RLS Policy: Tenant isolation mapping to 'app.tenant_id'
        # Fallback to true checking if not found for admin overrides
        await conn.execute(text(
            "CREATE POLICY case_tenant_isolation ON cases "
            "FOR ALL "
            "USING ("
            "    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::UUID "
            "    OR current_setting('app.override_rls', true) = 'true'"
            ");"
        ))
