"""
测试AkShare数据接口
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.stock_service import stock_service


async def test_all_interfaces():
    """测试所有数据接口"""
    test_code = "000001"  # 平安银行
    
    print("=" * 60)
    print("开始测试AkShare数据接口")
    print("=" * 60)
    
    # 1. 测试股票列表
    print("\n1. 测试获取股票列表...")
    stocks = await stock_service.get_stock_list(market="all")
    print(f"   ✓ 成功获取 {len(stocks)} 只股票")
    if stocks:
        print(f"   示例: {stocks[0]['code']} - {stocks[0]['name']}")
    
    # 2. 测试实时行情
    print(f"\n2. 测试获取实时行情 ({test_code})...")
    quote = await stock_service.get_realtime_quote(test_code)
    if quote:
        print(f"   ✓ {quote['name']} - 当前价: {quote['price']} 涨跌幅: {quote['change_pct']}%")
    else:
        print("   ✗ 获取失败")
    
    # 3. 测试K线数据
    print(f"\n3. 测试获取日K线数据 ({test_code})...")
    klines = await stock_service.get_kline_data(test_code, period="daily", count=5)
    if klines:
        print(f"   ✓ 成功获取 {len(klines)} 条K线数据")
        print(f"   最新: {klines[-1]['timestamp'].date()} 收盘价: {klines[-1]['close']}")
    else:
        print("   ✗ 获取失败")
    
    # 4. 测试市场概览
    print("\n4. 测试获取市场概览...")
    overview = await stock_service.get_market_overview()
    print(f"   ✓ 上涨: {overview['up_count']} 下跌: {overview['down_count']} 涨停: {overview['limit_up_count']}")
    
    # 5. 测试盘口数据
    print(f"\n5. 测试获取盘口数据 ({test_code})...")
    bid_ask = await stock_service.get_bid_ask_data(test_code)
    if bid_ask:
        print(f"   ✓ 买一: {bid_ask['bid1']} ({bid_ask['bid1_volume']}手)")
        print(f"   ✓ 卖一: {bid_ask['ask1']} ({bid_ask['ask1_volume']}手)")
    else:
        print("   ✗ 获取失败")
    
    # 6. 测试分时数据
    print(f"\n6. 测试获取分时数据 ({test_code})...")
    intraday = await stock_service.get_intraday_data(test_code)
    if intraday:
        print(f"   ✓ 成功获取 {len(intraday)} 条分时数据")
        print(f"   最新: {intraday[-1]['timestamp']} 价格: {intraday[-1]['price']}")
    else:
        print("   ✗ 获取失败(可能是非交易时间)")
    
    # 7. 测试分钟K线
    print(f"\n7. 测试获取分钟K线数据 ({test_code}, 5分钟)...")
    minute_klines = await stock_service.get_minute_kline(test_code, period="5", count=10)
    if minute_klines:
        print(f"   ✓ 成功获取 {len(minute_klines)} 条分钟K线数据")
        print(f"   最新: {minute_klines[-1]['timestamp']} 收盘价: {minute_klines[-1]['close']}")
    else:
        print("   ✗ 获取失败(可能是非交易时间)")
    
    # 8. 测试股票信息
    print(f"\n8. 测试获取股票信息 ({test_code})...")
    info = await stock_service.get_stock_info(test_code)
    if info:
        print(f"   ✓ {info['name']} - 行业: {info.get('industry', 'N/A')} 市值: {info.get('market_cap', 'N/A')}亿")
    else:
        print("   ✗ 获取失败")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_interfaces())
