from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.user import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", version="1.0.0")

app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "user-service ok"}