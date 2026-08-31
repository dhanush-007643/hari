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

        # Create and seed sample business tables if they do not exist
        try:
            # Check if products table exists
            table_check = await session.execute(
                text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='products'") if "sqlite" in async_db_url
                else text("SELECT count(*) FROM information_schema.tables WHERE table_name='products'")
            )
            has_products = table_check.scalar() > 0

            if not has_products:
                # Create Products Table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS products (
                        product_id INTEGER PRIMARY KEY,
                        product_name VARCHAR(255) NOT NULL,
                        category VARCHAR(100),
                        unit_price FLOAT,
                        stock_quantity INTEGER
                    );
                """))

                # Create Departments Table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS departments (
                        department_id INTEGER PRIMARY KEY,
                        department_name VARCHAR(100) NOT NULL,
                        manager VARCHAR(100),
                        location VARCHAR(100)
                    );
                """))

                # Create Customers Table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS customers (
                        customer_id INTEGER PRIMARY KEY,
                        customer_name VARCHAR(150) NOT NULL,
                        email VARCHAR(255),
                        city VARCHAR(100),
                        region VARCHAR(50),
                        segment VARCHAR(50)
                    );
                """))

                # Create Employees Table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS employees (
                        employee_id INTEGER PRIMARY KEY,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        email VARCHAR(255),
                        department_id INTEGER,
                        salary FLOAT,
                        hire_date VARCHAR(50),
                        performance_score FLOAT
                    );
                """))

                # Create Sales Orders Table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS sales_orders (
                        order_id INTEGER PRIMARY KEY,
                        customer_id INTEGER,
                        product_id INTEGER,
                        order_date VARCHAR(50),
                        quantity INTEGER,
                        unit_price FLOAT,
                        total_amount FLOAT,
                        region VARCHAR(50),
                        status VARCHAR(50)
                    );
                """))
                await session.commit()

                # Seed sample rows
                await session.execute(text("""
                    INSERT INTO products (product_id, product_name, category, unit_price, stock_quantity) VALUES
                    (101, 'DataVista AI Suite', 'Software', 499.00, 150),
                    (102, 'Cloud Storage Enterprise 1TB', 'Cloud Services', 120.00, 500),
                    (103, 'Real-time Analytics Sensor', 'Hardware', 250.00, 85),
                    (104, 'Executive BI Dashboard License', 'Software', 799.00, 200),
                    (105, 'Predictive ML Add-on', 'AI / ML', 350.00, 120);
                """))

                await session.execute(text("""
                    INSERT INTO departments (department_id, department_name, manager, location) VALUES
                    (1, 'Engineering', 'Alice Cooper', 'Building A - Floor 3'),
                    (2, 'Sales & Marketing', 'Bob Vance', 'Building B - Floor 1'),
                    (3, 'Data Science', 'Carol Danvers', 'Building A - Floor 4'),
                    (4, 'Executive & Operations', 'David Warner', 'Headquarters');
                """))

                await session.execute(text("""
                    INSERT INTO customers (customer_id, customer_name, email, city, region, segment) VALUES
                    (501, 'Acme Global Corp', 'contact@acme.com', 'New York', 'North', 'Enterprise'),
                    (502, 'Summit Financial Tech', 'ops@summitfin.com', 'Chicago', 'North', 'Enterprise'),
                    (503, 'Pacific Retail Group', 'procurement@pacific.com', 'San Francisco', 'West', 'Mid-Market'),
                    (504, 'Southern Logistics LLC', 'info@southernlog.com', 'Austin', 'South', 'SMB'),
                    (505, 'Atlantic Analytics Inc', 'team@atlantic.com', 'Boston', 'East', 'Enterprise');
                """))

                await session.execute(text("""
                    INSERT INTO employees (employee_id, first_name, last_name, email, department_id, salary, hire_date, performance_score) VALUES
                    (1, 'Sarah', 'Connor', 'sarah.c@datavista.com', 1, 115000, '2022-03-15', 4.9),
                    (2, 'John', 'Smith', 'john.s@datavista.com', 2, 85000, '2023-01-10', 4.5),
                    (3, 'Elena', 'Rostova', 'elena.r@datavista.com', 3, 125000, '2021-08-01', 4.8),
                    (4, 'Marcus', 'Aurelius', 'marcus.a@datavista.com', 1, 95000, '2023-06-20', 4.6),
                    (5, 'Jessica', 'Pearson', 'jessica.p@datavista.com', 4, 160000, '2020-05-12', 5.0);
                """))

                await session.execute(text("""
                    INSERT INTO sales_orders (order_id, customer_id, product_id, order_date, quantity, unit_price, total_amount, region, status) VALUES
                    (1001, 501, 101, '2024-01-15', 2, 499.00, 998.00, 'North', 'Completed'),
                    (1002, 502, 104, '2024-01-18', 1, 799.00, 799.00, 'North', 'Completed'),
                    (1003, 503, 102, '2024-02-01', 5, 120.00, 600.00, 'West', 'Completed'),
                    (1004, 504, 103, '2024-02-14', 3, 250.00, 750.00, 'South', 'Completed'),
                    (1005, 505, 105, '2024-02-20', 2, 350.00, 700.00, 'East', 'Completed'),
                    (1006, 501, 104, '2024-03-05', 2, 799.00, 1598.00, 'North', 'Completed'),
                    (1007, 503, 101, '2024-03-12', 1, 499.00, 499.00, 'West', 'Completed'),
                    (1008, 504, 102, '2024-03-22', 10, 120.00, 1200.00, 'South', 'Completed');
                """))
                await session.commit()
                logger.info("Sample business tables created and seeded for SQL Playground.")
        except Exception as seed_err:
            logger.warning(f"Note on seeding sample business tables: {seed_err}")
