"""
股票数据后备服务 - 当AkShare无法连接时使用模拟数据
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random


class DataFallbackService:
    """数据后备服务 - 提供模拟数据"""
    
    @staticmethod
    def generate_kline_data(code: str, count: int = 60) -> List[Dict[str, Any]]:
        """
        生成模拟K线数据
        
        Args:
            code: 股票代码
            count: 数据条数
        
        Returns:
            K线数据列表
        """
        klines = []
        base_price = 10.0 + random.uniform(-2, 2)  # 基础价格
        current_date = datetime.now() - timedelta(days=count)
        
        for i in range(count):
            # 生成随机波动
            change = random.uniform(-0.05, 0.05)
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = base_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.randint(500000, 2000000)
            
            klines.append({
                'timestamp': current_date + timedelta(days=i),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'turnover': round(volume * close_price, 2),
                'amplitude': round(abs(change) * 100, 2),
                'change_pct': round(change * 100, 2)
            })
            
            # 更新基础价格
            base_price = close_price
        
        return klines
    
    @staticmethod
    def generate_market_overview() -> Dict[str, Any]:
        """生成模拟市场概览"""
        total = random.randint(4000, 5000)
        up_count = random.randint(int(total * 0.3), int(total * 0.6))
        down_count = total - up_count - random.randint(50, 200)
        flat_count = total - up_count - down_count
        
        return {
            'up_count': up_count,
            'down_count': down_count,
            'flat_count': flat_count,
            'total_count': total,
            'limit_up_count': random.randint(20, 100),
            'limit_down_count': random.randint(5, 50),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def generate_stock_list(market: str = "all") -> List[Dict[str, Any]]:
        """生成模拟股票列表"""
        stocks = []
        stock_codes = {
            'sh': ['600000', '600001', '600002', '600003', '600004'],
            'sz': ['000001', '000002', '000003', '000004', '000005'],
        }
        
        codes = stock_codes.get('sh', []) + stock_codes.get('sz', []) if market == 'all' else stock_codes.get(market, [])
        
        for code in codes:
            base_price = random.uniform(5, 50)
            change_pct = random.uniform(-10, 10)
            
            stocks.append({
                'code': code,
                'name': f'股票{code}',
                'price': round(base_price, 2),
                'change_pct': round(change_pct, 2),
                'change': round(base_price * change_pct / 100, 2),
                'volume': random.randint(100000, 5000000),
                'turnover': random.uniform(1000000, 100000000),
                'amplitude': round(random.uniform(1, 10), 2),
                'high': round(base_price * 1.02, 2),
                'low': round(base_price * 0.98, 2),
                'open': round(base_price * random.uniform(0.98, 1.02), 2),
                'pre_close': round(base_price, 2)
            })
        
        return stocks
    
    @staticmethod
    def generate_realtime_quote(code: str) -> Dict[str, Any]:
        """
        生成模拟实时行情数据
        
        Args:
            code: 股票代码
        
        Returns:
            实时行情数据
        """
        base_price = 10.0 + random.uniform(-2, 2)
        change_pct = random.uniform(-5, 5)
        
        stock_names = {
            '000001': '平安银行',
            '000002': '万科A',
            '600000': '浦发银行',
            '600001': '邯郸钢铁',
        }
        
        return {
            'code': code,
            'name': stock_names.get(code, f'股票{code}'),
            'price': round(base_price, 2),
            'change_pct': round(change_pct, 2),
            'change': round(base_price * change_pct / 100, 2),
            'volume': random.randint(100000, 5000000),
            'turnover': round(random.uniform(1000000, 50000000), 2),
            'amplitude': round(random.uniform(1, 10), 2),
            'high': round(base_price * 1.02, 2),
            'low': round(base_price * 0.98, 2),
            'open': round(base_price * random.uniform(0.98, 1.02), 2),
            'pre_close': round(base_price * (1 - change_pct/100), 2)
        }
