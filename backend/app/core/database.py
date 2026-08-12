"""
DataVista+ Database Configuration
SQLAlchemy async engine, session management, and base model
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Async engine for API requests
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Sync engine for ML operations and report generation
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {},
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
    """Initialize the database — create all tables and run seed data."""
    from app.models import user_model, dataset_model, query_model, ml_model  # noqa
    from app.models import insight_model, report_model  # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")
    await _seed_initial_data()


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
