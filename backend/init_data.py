"""
初始化系统默认规则
"""
import asyncio
from sqlalchemy import select
from app.core import async_session_maker, init_db
from app.models import TradeRule


# 系统默认规则数据
DEFAULT_RULES = [
    # 排除规则
    {
        "name": "ST股排除",
        "category": "exclude",
        "rule_type": "filter",
        "condition": '{"field": "name", "operator": "not_contains", "value": ["ST", "退"]}',
        "description": "排除ST/*ST股、退市风险警示股",
        "is_system": True,
        "priority": 100
    },
    {
        "name": "市值过滤",
        "category": "exclude",
        "rule_type": "filter",
        "condition": '{"field": "market_cap", "operator": "between", "value": [20, 500]}',
        "description": "流通市值20亿~500亿",
        "is_system": True,
        "priority": 90
    },
    {
        "name": "利空排除",
        "category": "exclude",
        "rule_type": "filter",
        "condition": '{"field": "has_bad_news", "operator": "==", "value": false}',
        "description": "排除近3交易日重大利空个股",
        "is_system": True,
        "priority": 85
    },
    {
        "name": "僵尸股排除",
        "category": "exclude",
        "rule_type": "filter",
        "condition": '{"field": "turnover", "operator": ">=", "value": 10000000}',
        "description": "排除近20日无涨停/无放量个股",
        "is_system": True,
        "priority": 80
    },
    # 核心标的规则
    {
        "name": "放量长上影",
        "category": "core",
        "rule_type": "signal",
        "condition": '{"amplitude": ">=5", "turnover": ">=100000000", "upper_shadow_ratio": ">=0.5"}',
        "description": "上影线≥50%振幅，量≥2倍均量",
        "is_system": True,
        "priority": 70
    },
    {
        "name": "一进二接力",
        "category": "core",
        "rule_type": "signal",
        "condition": '{"change_pct": "3-7", "turnover": ">=50000000", "is_first_board_next": true}',
        "description": "首板后第1交易日，市值≤100亿",
        "is_system": True,
        "priority": 65
    },
    {
        "name": "抗跌强势股",
        "category": "core",
        "rule_type": "signal",
        "condition": '{"change_pct": "-2~2", "amplitude": "<5", "market_trend": "down"}',
        "description": "大盘跌时个股拒绝跟跌",
        "is_system": True,
        "priority": 60
    },
    # 风控规则
    {
        "name": "最大止损比例",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"stop_loss_pct": 8}',
        "description": "单笔交易最大浮亏止损线",
        "is_system": True,
        "priority": 100
    },
    {
        "name": "止盈阶梯1",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"take_profit_pct": 3, "action": "alert"}',
        "description": "浮盈达到3%触发第一级止盈提醒",
        "is_system": True,
        "priority": 90
    },
    {
        "name": "止盈阶梯2",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"take_profit_pct": 5, "action": "partial_sell"}',
        "description": "浮盈达到5%触发第二级止盈",
        "is_system": True,
        "priority": 85
    },
    {
        "name": "止盈阶梯3",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"take_profit_pct": 10, "action": "trailing_stop"}',
        "description": "浮盈达到10%触发移动止盈",
        "is_system": True,
        "priority": 80
    },
    {
        "name": "连续亏损限仓",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"consecutive_loss_days": 3, "position_limit": 0.3}',
        "description": "连续亏损交易日后限制仓位至30%",
        "is_system": True,
        "priority": 75
    },
    {
        "name": "单日最大回撤",
        "category": "risk",
        "rule_type": "risk",
        "condition": '{"max_drawdown_pct": 5}',
        "description": "单日账户最大回撤预警线",
        "is_system": True,
        "priority": 95
    }
]


async def init_default_rules():
    """初始化默认规则"""
    async with async_session_maker() as session:
        # 检查是否已初始化
        result = await session.execute(
            select(TradeRule).where(TradeRule.is_system == True).limit(1)
        )
        if result.scalar_one_or_none():
            print("系统规则已存在，跳过初始化")
            return
        
        # 插入默认规则
        for rule_data in DEFAULT_RULES:
            rule = TradeRule(**rule_data)
            session.add(rule)
        
        await session.commit()
        print(f"成功初始化 {len(DEFAULT_RULES)} 条系统默认规则")


async def main():
    """主函数"""
    print("开始初始化...")
    
    # 初始化数据库
    await init_db()
    print("数据库初始化完成")
    
    # 初始化默认规则
    await init_default_rules()
    
    print("初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
