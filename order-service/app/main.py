from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.orders import router as orders_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order Service", version="1.0.0")

app.include_router(orders_router)


@app.get("/health")
def health():
    return {"status": "order-service ok"}