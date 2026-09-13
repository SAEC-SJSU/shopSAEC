from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import close_db, connect_db
from routes.orders import router as orders_router
from routes.stock import router as stock_router, seed_stock
from routes.manager import router as manager_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await seed_stock()
    yield
    await close_db()


_is_prod = settings.ENV != "dev"

# Swagger/ReDoc/openapi.json hand an attacker the full API map, and the backend
# port is reachable directly if the origin firewall ever lapses. Dev only.
app = FastAPI(
    title="SAEC Shop API",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "https://shop.we-saec.me",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(stock_router, prefix="/api/stock", tags=["stock"])
app.include_router(manager_router, prefix="/api/manager", tags=["manager"])


