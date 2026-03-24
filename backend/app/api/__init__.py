"""
API路由模块
"""
from fastapi import APIRouter
from app.api.stocks import router as stocks_router
from app.api.positions import router as positions_router
from app.api.rules import router as rules_router
from app.api.signals import router as signals_router

api_router = APIRouter()
api_router.include_router(stocks_router)
api_router.include_router(positions_router)
api_router.include_router(rules_router)
api_router.include_router(signals_router)
