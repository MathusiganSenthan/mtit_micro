from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.notifications import router as notifications_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service", version="1.0.0")

app.include_router(notifications_router)


@app.get("/health")
def health():
    return {"status": "notification-service ok"}