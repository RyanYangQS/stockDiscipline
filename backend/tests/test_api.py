"""
API接口测试
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def async_client():
    """异步客户端fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_root(async_client):
    """测试根路径"""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "镇金仓"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check(async_client):
    """测试健康检查"""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_screening_api(async_client):
    """测试选股API"""
    response = await async_client.post(
        "/api/stock/screening",
        json={
            "rules": ["exclude_st", "market_cap"],
            "market": "all",
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert "screened_at" in data


@pytest.mark.asyncio
async def test_kline_api(async_client):
    """测试K线API"""
    response = await async_client.get("/api/stock/kline/000001?period=daily&count=10")
    # 注意：实际测试可能需要mock数据
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_market_overview(async_client):
    """测试市场概览API"""
    response = await async_client.get("/api/stock/market/overview")
    assert response.status_code == 200
    data = response.json()
    assert "up_count" in data
    assert "down_count" in data
    assert "total_count" in data
