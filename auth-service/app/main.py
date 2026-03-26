from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.auth import router as auth_router

# Create tables on startup (use Alembic for production migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="1.0.0")

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "auth-service ok"}