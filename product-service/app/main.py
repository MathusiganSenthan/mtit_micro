from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes.products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product Service", version="1.0.0")

app.include_router(products_router)


@app.get("/health")
def health():
    return {"status": "product-service ok"}