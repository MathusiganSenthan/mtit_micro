from fastapi import FastAPI
from app.routes import router
 
app = FastAPI(title="Bookstore API Gateway", version="1.0.0")
 
app.include_router(router)
 
 
@app.get("/health")
def health():
    return {"status": "gateway ok"}