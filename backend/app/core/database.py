"""
DataVista+ Database Configuration
SQLAlchemy async engine, session management, and base model with robust fallback
"""
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from app.core.config import settings

logger = logging.getLogger(__name__)

def _normalize_async_url(url: str) -> str:
    if not url:
        return "sqlite+aiosqlite:///./datavista.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _normalize_sync_url(url: str) -> str:
    if not url:
        return "sqlite:///./datavista.db"
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


# Determine database URL
raw_db_url = settings.DATABASE_URL or "sqlite+aiosqlite:///./datavista.db"

# If in production/Render and DATABASE_URL points to localhost (which won't exist in Render container), fallback to SQLite
is_cloud_env = bool(os.getenv("RENDER") or os.getenv("PORT") or not settings.DEBUG)
if is_cloud_env and ("localhost" in raw_db_url or "127.0.0.1" in raw_db_url):
    logger.warning("Detected localhost DB URL in cloud environment. Falling back to SQLite database.")
    raw_db_url = "sqlite+aiosqlite:///./datavista.db"

async_db_url = _normalize_async_url(raw_db_url)
sync_db_url = _normalize_sync_url(settings.SYNC_DATABASE_URL or raw_db_url)

# Async engine for API requests
engine = create_async_engine(
    async_db_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in async_db_url else {},
)

# Sync engine for ML operations and report generation
sync_engine = create_engine(
    sync_db_url,
    connect_args={"check_same_thread": False} if "sqlite" in sync_db_url else {},
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    Used in FastAPI route handlers via Depends(get_db).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize the database — create all tables and run seed data with resilient error handling."""
    global engine, sync_engine, AsyncSessionLocal
    from app.models import user_model, dataset_model, query_model, ml_model  # noqa
    from app.models import insight_model, report_model  # noqa

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
        await _seed_initial_data()
    except Exception as e:
        logger.error(f"Failed to connect to primary database ({async_db_url}): {e}")
        # If remote/local postgres fails, gracefully fallback to SQLite so the app never crashes
        if "sqlite" not in async_db_url:
            logger.warning("Falling back to embedded SQLite database (datavista.db)...")
            fallback_async = "sqlite+aiosqlite:///./datavista.db"
            fallback_sync = "sqlite:///./datavista.db"
            
            engine = create_async_engine(
                fallback_async,
                echo=False,
                connect_args={"check_same_thread": False},
            )
            sync_engine = create_engine(
                fallback_sync,
                connect_args={"check_same_thread": False},
            )
            AsyncSessionLocal = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Fallback SQLite database initialized successfully.")
            await _seed_initial_data()
        else:
            raise e


async def _seed_initial_data():
    """Seed initial roles, admin user, and sample data if not already present."""
    from sqlalchemy import text
    from app.models.user_model import User, Role
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE username='admin'")
        )
        count = result.scalar()
        if count == 0:
            # Create roles
            roles = [
                Role(id=1, name="admin", description="Full system access"),
                Role(id=2, name="analyst", description="Analytics and query access"),
                Role(id=3, name="viewer", description="Read-only access"),
                Role(id=4, name="data_scientist", description="ML access"),
            ]
            session.add_all(roles)
            await session.flush()

            # Create admin user
            admin = User(
                username="admin",
                email="admin@datavista.com",
                hashed_password=get_password_hash("Admin@123"),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                role_id=1,
            )
            session.add(admin)
            await session.commit()
            logger.info("Admin user created: admin@datavista.com / Admin@123")
