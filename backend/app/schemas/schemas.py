"""
Pydantic Schemas - API请求和响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 股票相关 ====================

class StockBase(BaseModel):
    """股票基础模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")


class StockResponse(StockBase):
    """股票响应模型"""
    id: int
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    is_st: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 选股相关 ====================

class ScreeningRequest(BaseModel):
    """选股请求模型"""
    rules: List[str] = Field(default_factory=list, description="规则ID列表")
    market: str = Field(default="all", description="市场筛选: all/sh/sz")
    sort_by: str = Field(default="score", description="排序字段")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")


class StockPoolItem(BaseModel):
    """选股池项"""
    code: str
    name: str
    price: float
    change_pct: float
    signal_type: str
    score: int
    volume_ratio: Optional[float] = None
    reason: Optional[str] = None


class ScreeningResponse(BaseModel):
    """选股响应模型"""
    total: int
    items: List[StockPoolItem]
    screened_at: datetime


# ==================== K线相关 ====================

class KLineRequest(BaseModel):
    """K线请求模型"""
    code: str = Field(..., description="股票代码")
    period: str = Field(default="daily", description="周期: daily/weekly/minute")
    count: int = Field(default=60, ge=1, le=500, description="数据条数")


class KLineItem(BaseModel):
    """K线数据项"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: Optional[float] = None


class KLineResponse(BaseModel):
    """K线响应模型"""
    code: str
    name: str
    period: str
    data: List[KLineItem]


# ==================== 持仓相关 ====================

class PositionCreate(BaseModel):
    """创建持仓请求"""
    stock_code: str
    stock_name: str
    cost_price: float = Field(..., gt=0, description="成本价")
    quantity: int = Field(..., gt=0, description="持仓数量")
    buy_date: datetime


class PositionResponse(BaseModel):
    """持仓响应模型"""
    id: int
    stock_code: str
    stock_name: str
    cost_price: float
    quantity: int
    current_price: Optional[float] = None
    profit: Optional[float] = None
    profit_pct: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    status: str
    
    class Config:
        from_attributes = True


# ==================== 信号相关 ====================

class SignalResponse(BaseModel):
    """信号响应模型"""
    id: int
    stock_code: str
    signal_type: str
    signal_name: str
    price: float
    priority: str
    reason: Optional[str] = None
    is_triggered: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 规则相关 ====================

class RuleCreate(BaseModel):
    """创建规则请求"""
    name: str
    category: str
    rule_type: str
    condition: str
    description: Optional[str] = None


class RuleResponse(BaseModel):
    """规则响应模型"""
    id: int
    name: str
    category: str
    rule_type: str
    condition: str
    description: Optional[str] = None
    is_system: bool
    is_enabled: bool
    priority: int
    
    class Config:
        from_attributes = True


# ==================== 市场概览 ====================

class IndexInfo(BaseModel):
    """大盘指数信息"""
    name: str = Field(..., description="指数名称")
    code: str = Field(..., description="指数代码")
    price: float = Field(..., description="当前点位")
    change: float = Field(..., description="涨跌点数")
    change_pct: float = Field(..., description="涨跌幅%")


class MarketOverview(BaseModel):
    """市场概览响应"""
    up_count: int = Field(..., description="上涨家数")
    down_count: int = Field(..., description="下跌家数")
    flat_count: int = Field(..., description="平盘家数")
    total_count: int = Field(..., description="总股票数")
    limit_up_count: int = Field(..., description="涨停数")
    limit_down_count: int = Field(..., description="跌停数")
    indices: List[IndexInfo] = Field(default=[], description="大盘指数列表")
    updated_at: datetime


# ==================== 盘口数据 ====================

class BidAskResponse(BaseModel):
    """盘口数据响应(买卖五档)"""
    code: str = Field(..., description="股票代码")
    bid1: Optional[float] = Field(None, description="买一价")
    bid1_volume: Optional[int] = Field(None, description="买一量")
    bid2: Optional[float] = Field(None, description="买二价")
    bid2_volume: Optional[int] = Field(None, description="买二量")
    bid3: Optional[float] = Field(None, description="买三价")
    bid3_volume: Optional[int] = Field(None, description="买三量")
    bid4: Optional[float] = Field(None, description="买四价")
    bid4_volume: Optional[int] = Field(None, description="买四量")
    bid5: Optional[float] = Field(None, description="买五价")
    bid5_volume: Optional[int] = Field(None, description="买五量")
    ask1: Optional[float] = Field(None, description="卖一价")
    ask1_volume: Optional[int] = Field(None, description="卖一量")
    ask2: Optional[float] = Field(None, description="卖二价")
    ask2_volume: Optional[int] = Field(None, description="卖二量")
    ask3: Optional[float] = Field(None, description="卖三价")
    ask3_volume: Optional[int] = Field(None, description="卖三量")
    ask4: Optional[float] = Field(None, description="卖四价")
    ask4_volume: Optional[int] = Field(None, description="卖四量")
    ask5: Optional[float] = Field(None, description="卖五价")
    ask5_volume: Optional[int] = Field(None, description="卖五量")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 分时数据 ====================

class IntradayItem(BaseModel):
    """分时数据项"""
    timestamp: datetime = Field(..., description="时间戳")
    price: float = Field(..., description="价格")
    volume: int = Field(..., description="成交量")
    avg_price: Optional[float] = Field(None, description="均价")


class IntradayResponse(BaseModel):
    """分时数据响应"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    data: List[IntradayItem] = Field(..., description="分时数据列表")


# ==================== 分钟K线 ====================

class MinuteKLineRequest(BaseModel):
    """分钟K线请求模型"""
    code: str = Field(..., description="股票代码")
    period: str = Field(default="5", description="周期: 1/5/15/30/60分钟")
    count: int = Field(default=48, ge=1, le=240, description="数据条数")


class MinuteKLineItem(BaseModel):
    """分钟K线数据项"""
    timestamp: datetime = Field(..., description="时间戳")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    turnover: Optional[float] = Field(None, description="成交额")


class MinuteKLineResponse(BaseModel):
    """分钟K线响应模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    period: str = Field(..., description="周期")
    data: List[MinuteKLineItem] = Field(..., description="分钟K线数据")
