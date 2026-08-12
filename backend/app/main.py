"""
DataVista+ FastAPI Application
Main entry point with middleware, CORS, routers, and OpenAPI documentation
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import settings
from app.core.database import init_db

# API Routers
from app.api import auth, queries, analytics, ml, insights, reports, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
        ## DataVista+ — Explainable AI-Powered Decision Intelligence Platform

        A production-ready enterprise platform enabling:
        - 🗣️ **Natural Language Queries** → SQL conversion
        - 📊 **Interactive Analytics** Dashboards with KPIs and charts
        - 🤖 **Explainable AI** with SHAP & LIME explanations
        - 🔮 **Predictive Analytics** with auto model selection
        - 💡 **Automated Business Insights** and Recommendations
        - 📄 **Report Generation** in PDF, Excel, and CSV

        ### Authentication
        All endpoints require JWT Bearer token authentication.
        Obtain tokens via `/api/v1/auth/login`.

        **Default admin credentials:** `admin@datavista.com` / `Admin@123`
        """,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ─── Middleware ──────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"
        return response

    # ─── Routers ────────────────────────────────────────────────────────────
    prefix = settings.API_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(queries.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(ml.router, prefix=prefix)
    app.include_router(insights.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)

    # ─── Events ─────────────────────────────────────────────────────────────
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 DataVista+ starting up...")
        await init_db()
        logger.info("✅ Database initialized")
        logger.info(f"📚 API docs: http://localhost:8092{app.docs_url}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 DataVista+ shutting down...")

    # ─── Root Endpoints ──────────────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}

    # ─── Exception Handlers ──────────────────────────────────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(status_code=404, content={"detail": "Resource not found"})

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8092,
        reload=settings.DEBUG,
        log_level="info",
    )
