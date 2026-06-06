import os
import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from dotenv import load_dotenv

load_dotenv()

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    environment=os.getenv("ENV", "development"),
    release="shopflow@1.2.3",
    traces_sample_rate=1.0,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
)

from db import init_db
from routes import products, checkout, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed products if the table is empty
    from db import SessionLocal
    from models import Product
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            import seed
            seed.run(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="ShopFlow API",
    description="E-commerce backend for ShopFlow",
    version="1.2.3",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.2.3", "env": os.getenv("ENV", "development")}


@app.get("/sentry-debug")
async def trigger_error():
    if os.getenv("ENV", "development").lower() == "production":
        raise HTTPException(status_code=404, detail="Not found")
    division_by_zero = 1 / 0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8001)), reload=True)
