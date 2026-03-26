from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.feedback import router as feedback_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Feedback Service", version="1.0.0")

app.include_router(feedback_router)


@app.get("/health")
def health():
    return {"status": "feedback-service ok"}