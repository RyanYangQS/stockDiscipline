"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, comment="股票代码")
    name: Mapped[str] = mapped_column(String(50), comment="股票名称")
    market: Mapped[str] = mapped_column(String(10), comment="市场: sh/sz")
    industry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="所属行业")
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通市值(亿)")
    is_st: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否ST股")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class StockPool(Base):
    """选股池表"""
    __tablename__ = "stock_pool"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), comment="股票代码")
    signal_type: Mapped[str] = mapped_column(String(50), comment="信号类型: 放量长上影/一进二/抗跌强势")
    score: Mapped[int] = mapped_column(Integer, default=0, comment="匹配度评分")
    price: Mapped[float] = mapped_column(Float, comment="入选时价格")
    change_pct: Mapped[float] = mapped_column(Float, comment="入选时涨跌幅")
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="量比")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="入选原因")
    pool_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="入选日期")
    is_watched: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已关注")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Position(Base):
    """持仓表"""
    __tablename__ = "positions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), comment="股票代码")
    stock_name: Mapped[str] = mapped_column(String(50), comment="股票名称")
    cost_price: Mapped[float] = mapped_column(Float, comment="成本价")
    quantity: Mapped[int] = mapped_column(Integer, comment="持仓数量")
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当前价")
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈亏金额")
    profit_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈亏比例")
    stop_loss_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="止损价")
    take_profit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="止盈价")
    buy_date: Mapped[datetime] = mapped_column(DateTime, comment="买入日期")
    status: Mapped[str] = mapped_column(String(20), default="holding", comment="状态: holding/sold")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class TradeRule(Base):
    """交易规则表"""
    __tablename__ = "trade_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="规则名称")
    category: Mapped[str] = mapped_column(String(50), comment="规则分类: exclude/core/custom/risk")
    rule_type: Mapped[str] = mapped_column(String(50), comment="规则类型: filter/signal/risk")
    condition: Mapped[str] = mapped_column(Text, comment="规则条件(JSON)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="规则说明")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统规则")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Signal(Base):
    """买卖信号表"""
    __tablename__ = "signals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), comment="股票代码")
    signal_type: Mapped[str] = mapped_column(String(50), comment="信号类型: buy/sell/warn")
    signal_name: Mapped[str] = mapped_column(String(100), comment="信号名称")
    price: Mapped[float] = mapped_column(Float, comment="信号价格")
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", comment="优先级: HIGH/MEDIUM/LOW")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="触发原因")
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已触发")
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="触发时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class KLineData(Base):
    """K线数据缓存表"""
    __tablename__ = "kline_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), comment="股票代码")
    trade_date: Mapped[datetime] = mapped_column(DateTime, comment="交易日期")
    open_price: Mapped[float] = mapped_column(Float, comment="开盘价")
    high_price: Mapped[float] = mapped_column(Float, comment="最高价")
    low_price: Mapped[float] = mapped_column(Float, comment="最低价")
    close_price: Mapped[float] = mapped_column(Float, comment="收盘价")
    volume: Mapped[int] = mapped_column(Integer, comment="成交量")
    turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额")
    amplitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="振幅")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
