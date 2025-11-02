from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import documents
from app.utils import REQUEST_PER_MINUTE


app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter = RateLimitMiddleware(REQUEST_PER_MINUTE)
app.middleware("http")(rate_limiter)

app.state.rate_limiter = rate_limiter

app.include_router(
    documents.router,
    prefix=f"{settings.prefix}/documents",
    tags=["documents"],
)


@app.get("/")
async def root():
    return {
        "message": f"{settings.name} is up and running ;)",
        "version": settings.version,
    }
