from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.weather import router as weather_router
from app.core.logging import configure_logging
from app.core.settings import settings

configure_logging()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(weather_router)
app.include_router(recommendations_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}
