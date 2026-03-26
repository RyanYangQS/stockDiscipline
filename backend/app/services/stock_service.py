"""
股票数据服务 - 对接pytdx（通达信）
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from app.core.config import settings
from pytdx.hq import TdxHq_API
import pandas as pd

# 禁用代理
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)


# 通达信服务器列表
TDX_SERVERS = [
    ('119.147.212.81', 7709),
    ('14.215.128.18', 7709),
    ('59.173.18.140', 7709),
    ('180.153.18.170', 7709),
    ('180.153.18.171', 7709),
    ('180.153.39.51', 7709),
    ('218.75.126.9', 7709),
    ('115.238.56.198', 7709),
    ('115.238.90.165', 7709),
    ('124.160.88.183', 7709),
    ('60.12.136.250', 7709),
    ('60.19.203.173', 7709),
    ('61.152.249.86', 7709),
]


class StockDataService:
    """股票数据服务类 - 使用pytdx"""
    
    def __init__(self):
        """初始化服务"""
        self.cache = {}
        self.cache_timeout = 300  # 缓存5分钟
        self.use_fallback = not settings.USE_REAL_DATA
        self._api = None
        self._connected = False
        self._stock_names = {}  # 股票名称缓存
    
    def _load_stock_names(self):
        """加载股票名称缓存"""
        if self._stock_names:
            return
        
        try:
            api = self._get_api()
            if not self._connected:
                return
            
            # 获取深圳股票名称
            for start in range(0, 5000, 1000):
                batch = api.get_security_list(0, start)
                if batch:
                    for item in batch:
                        code = item['code']
                        if code.startswith(('00', '30')):
                            self._stock_names[code] = item['name'].strip()
            
            # 获取上海股票名称
            for start in range(0, 5000, 1000):
                batch = api.get_security_list(1, start)
                if batch:
                    for item in batch:
                        code = item['code']
                        if code.startswith(('60', '68')):
                            self._stock_names[code] = item['name'].strip()
            
            logger.info(f"已缓存 {len(self._stock_names)} 个股票名称")
            
        except Exception as e:
            logger.error(f"加载股票名称失败: {e}")
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        # 先尝试从缓存获取
        if code in self._stock_names:
            return self._stock_names[code]
        
        # 缓存为空则加载
        self._load_stock_names()
        
        return self._stock_names.get(code, f'股票{code}')
    
    def _get_api(self, reconnect: bool = False) -> TdxHq_API:
        """
        获取pytdx API连接
        
        Args:
            reconnect: 是否强制重连
        """
        if reconnect:
            self._connected = False
            self._api = None
        
        if self._api is None or not self._connected:
            self._api = TdxHq_API()
            self._connected = False
            # 尝试连接服务器
            for host, port in TDX_SERVERS:
                try:
                    if self._api.connect(host, port):
                        self._connected = True
                        logger.info(f"pytdx连接成功: {host}:{port}")
                        # 重新加载股票名称缓存
                        self._stock_names = {}
                        self._load_stock_names()
                        break
                except Exception as e:
                    logger.warning(f"pytdx连接失败 {host}:{port}: {e}")
                    continue
            
            if not self._connected:
                logger.error("pytdx无法连接任何服务器")
        
        return self._api
    
    def _reconnect(self):
        """重新连接pytdx"""
        logger.info("尝试重新连接pytdx...")
        return self._get_api(reconnect=True)
    
    def _get_market_code(self, code: str) -> int:
        """
        根据股票代码获取市场代码
        
        Args:
            code: 股票代码
        
        Returns:
            市场代码 0=深圳, 1=上海
        """
        if code.startswith(('60', '68')):
            return 1  # 上海
        else:
            return 0  # 深圳
    
    def _format_code(self, code: str) -> str:
        """格式化股票代码（补全6位）"""
        return code.zfill(6)
    
    async def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表
        
        Args:
            market: 市场筛选 all/sh/sz
        
        Returns:
            股票列表
        """
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟股票列表 {market}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_stock_list(market)
        
        try:
            api = self._get_api()
            stocks = []
            
            # 获取深圳股票
            if market in ['all', 'sz']:
                count = api.get_security_count(0)
                for start in range(0, count, 1000):
                    batch = api.get_security_list(0, start)
                    if batch:
                        for item in batch:
                            code = item['code']
                            # 过滤非股票（指数、基金等）
                            if code.startswith(('00', '30')):
                                stocks.append({
                                    'code': code,
                                    'name': item['name'].strip(),
                                    'market': 'sz'
                                })
            
            # 获取上海股票
            if market in ['all', 'sh']:
                count = api.get_security_count(1)
                for start in range(0, count, 1000):
                    batch = api.get_security_list(1, start)
                    if batch:
                        for item in batch:
                            code = item['code']
                            # 过滤非股票
                            if code.startswith(('60', '68')):
                                stocks.append({
                                    'code': code,
                                    'name': item['name'].strip(),
                                    'market': 'sh'
                                })
            
            logger.info(f"从pytdx获取股票列表成功: {len(stocks)}条")
            return stocks
            
        except Exception as e:
            logger.error(f"从pytdx获取股票列表失败: {e}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_stock_list(market)
    
    async def get_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            code: 股票代码
        
        Returns:
            实时行情数据
        """
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟实时行情 {code}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_realtime_quote(code)
        
        try:
            api = self._get_api()
            market = self._get_market_code(code)
            formatted_code = self._format_code(code)
            
            # 获取行情数据
            data = api.get_security_quotes([(market, formatted_code)])
            
            # 如果没有数据，尝试重连一次
            if not data or len(data) == 0:
                logger.warning(f"pytdx未获取到实时行情 {code}，尝试重连...")
                api = self._reconnect()
                if self._connected:
                    data = api.get_security_quotes([(market, formatted_code)])
            
            if not data or len(data) == 0:
                return None
            
            item = data[0]
            pre_close = item['last_close'] if item['last_close'] > 0 else item['price']
            
            # 如果price为0（非交易时间），使用昨收价
            price = float(item['price']) if item['price'] and item['price'] > 0 else float(pre_close)
            high = float(item['high']) if item['high'] and item['high'] > 0 else price
            low = float(item['low']) if item['low'] and item['low'] > 0 else price
            open_price = float(item['open']) if item['open'] and item['open'] > 0 else price
            
            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0
            
            return {
                'code': code,
                'name': self._get_stock_name(code),
                'price': price,
                'change_pct': round(change_pct, 2),
                'change': round(change, 2),
                'volume': int(item['vol']) if item['vol'] else 0,
                'turnover': float(item['amount']) if item['amount'] else 0.0,
                'amplitude': 0.0,  # pytdx不直接提供振幅
                'high': high,
                'low': low,
                'open': open_price,
                'pre_close': float(pre_close)
            }
            
        except Exception as e:
            logger.error(f"从pytdx获取实时行情失败 {code}: {e}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_realtime_quote(code)
    
    async def get_kline_data(
        self, 
        code: str, 
        period: str = "daily", 
        count: int = 60
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            period: 周期 daily/weekly
            count: 数据条数
        
        Returns:
            K线数据列表
        """
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟K线数据 {code}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_kline_data(code, count)
        
        try:
            api = self._get_api()
            market = self._get_market_code(code)
            formatted_code = self._format_code(code)
            
            # pytdx K线周期: 9=日线, 5=周线, 6=月线
            kline_type = 9 if period == 'daily' else 5
            
            # 获取K线数据
            data = api.get_security_bars(kline_type, market, formatted_code, 0, count)
            
            # 如果没有数据，尝试重连一次
            if not data:
                logger.warning(f"pytdx未获取到K线数据 {code}，尝试重连...")
                api = self._reconnect()
                if self._connected:
                    data = api.get_security_bars(kline_type, market, formatted_code, 0, count)
            
            if not data:
                logger.warning(f"pytdx未获取到K线数据 {code}")
                from app.services.data_fallback import DataFallbackService
                return DataFallbackService.generate_kline_data(code, count)
            
            klines = []
            for item in reversed(data):  # pytdx返回的是倒序的
                klines.append({
                    'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M'),
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(item['vol']),
                    'turnover': float(item['amount']) if item.get('amount') else None,
                })
            
            logger.info(f"从pytdx获取K线数据成功: {code}, {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"从pytdx获取K线数据失败 {code}: {e}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_kline_data(code, count)
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览
        
        Returns:
            市场概览数据
        """
        if self.use_fallback:
            logger.info("开发模式: 使用模拟市场概览")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_market_overview()
        
        try:
            api = self._get_api()
            
            # 获取指数行情
            indices = []
            index_list = [
                (1, '000001'),  # 上证指数
                (0, '399001'),  # 深证成指
                (0, '399006'),  # 创业板指
            ]
            index_names = {
                '000001': '上证指数',
                '399001': '深证成指',
                '399006': '创业板指',
            }
            
            quotes = api.get_security_quotes(index_list)
            if quotes:
                for item in quotes:
                    code = item['code']
                    pre_close = item['last_close'] if item['last_close'] > 0 else item['price']
                    # 如果price为0（非交易时间），使用昨收价
                    price = float(item['price']) if item['price'] and item['price'] > 0 else float(pre_close)
                    change = price - pre_close if pre_close > 0 else 0
                    change_pct = (change / pre_close * 100) if pre_close > 0 else 0
                    
                    indices.append({
                        'name': index_names.get(code, code),
                        'code': code,
                        'price': price,
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2)
                    })
            
            # 获取涨跌统计（简化版，实际需要遍历所有股票）
            up_count = 0
            down_count = 0
            flat_count = 0
            limit_up_count = 0
            limit_down_count = 0
            
            # 采样统计（取前500只股票）
            sample_codes = []
            
            # 深圳采样
            for start in range(0, 500, 80):
                batch = api.get_security_list(0, start)
                if batch:
                    for item in batch:
                        if item['code'].startswith(('00', '30')):
                            sample_codes.append((0, item['code']))
                            if len(sample_codes) >= 250:
                                break
                if len(sample_codes) >= 250:
                    break
            
            # 上海采样
            for start in range(0, 500, 80):
                batch = api.get_security_list(1, start)
                if batch:
                    for item in batch:
                        if item['code'].startswith(('60', '68')):
                            sample_codes.append((1, item['code']))
                            if len(sample_codes) >= 500:
                                break
                if len(sample_codes) >= 500:
                    break
            
            # 获取采样股票行情
            if sample_codes:
                quotes = api.get_security_quotes(sample_codes)
                if quotes:
                    for item in quotes:
                        if item['price'] <= 0 or item['last_close'] <= 0:
                            continue
                        change_pct = (item['price'] - item['last_close']) / item['last_close'] * 100
                        
                        if change_pct > 0:
                            up_count += 1
                            if change_pct >= 9.9:
                                limit_up_count += 1
                        elif change_pct < 0:
                            down_count += 1
                            if change_pct <= -9.9:
                                limit_down_count += 1
                        else:
                            flat_count += 1
            
            logger.info(f"从pytdx获取市场概览成功")
            return {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'total_count': up_count + down_count + flat_count,
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'indices': indices,
                'updated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"从pytdx获取市场概览失败: {e}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_market_overview()
    
    async def get_intraday_data(self, code: str) -> List[Dict[str, Any]]:
        """
        获取分时数据
        
        Args:
            code: 股票代码
        
        Returns:
            分时数据列表
        """
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟分时数据 {code}")
            return []
        
        try:
            api = self._get_api()
            market = self._get_market_code(code)
            formatted_code = self._format_code(code)
            
            # 获取1分钟K线数据（当天）
            data = api.get_security_bars(8, market, formatted_code, 0, 240)
            
            # 如果没有数据，尝试重连一次
            if not data:
                logger.warning(f"pytdx未获取到分时数据 {code}，尝试重连...")
                api = self._reconnect()
                if self._connected:
                    data = api.get_security_bars(8, market, formatted_code, 0, 240)
            
            if not data:
                return []
            
            intraday = []
            # 计算均价
            total_amount = 0
            total_volume = 0
            
            for item in reversed(data):
                total_amount += item['amount']
                total_volume += item['vol']
                avg_price = total_amount / total_volume if total_volume > 0 else item['close']
                
                intraday.append({
                    'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M'),
                    'price': float(item['close']),
                    'volume': int(item['vol']),
                    'avg_price': float(avg_price)
                })
            
            logger.info(f"从pytdx获取分时数据成功: {code}, {len(intraday)}条")
            return intraday
            
        except Exception as e:
            logger.error(f"从pytdx获取分时数据失败 {code}: {e}")
            return []
    
    async def get_minute_kline(
        self, 
        code: str, 
        period: str = "5", 
        count: int = 48
    ) -> List[Dict[str, Any]]:
        """
        获取分钟K线数据
        
        Args:
            code: 股票代码
            period: 周期 1/5/15/30/60分钟
            count: 数据条数
        
        Returns:
            分钟K线数据列表
        """
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟分钟K线数据 {code}")
            return []
        
        try:
            api = self._get_api()
            market = self._get_market_code(code)
            formatted_code = self._format_code(code)
            
            # pytdx分钟周期映射
            period_map = {
                '1': 8,    # 1分钟
                '5': 0,    # 5分钟
                '15': 1,   # 15分钟
                '30': 2,   # 30分钟
                '60': 3,   # 60分钟
            }
            kline_type = period_map.get(period, 0)
            
            # 获取分钟K线数据
            data = api.get_security_bars(kline_type, market, formatted_code, 0, count)
            
            if not data:
                return []
            
            klines = []
            for item in reversed(data):
                klines.append({
                    'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M'),
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(item['vol']),
                    'turnover': float(item['amount']) if item.get('amount') else None
                })
            
            logger.info(f"从pytdx获取分钟K线数据成功: {code}, {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"从pytdx获取分钟K线数据失败 {code}: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票详细信息
        
        Args:
            code: 股票代码
        
        Returns:
            股票信息
        """
        try:
            # 获取实时行情作为基本信息
            quote = await self.get_realtime_quote(code)
            if quote:
                return {
                    'code': code,
                    'name': quote['name'],
                    'industry': '',
                    'market_cap': None,
                    'is_st': 'ST' in quote['name'] or '*' in quote['name']
                }
            return None
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_bid_ask_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取盘口数据(买卖五档)
        
        Args:
            code: 股票代码
        
        Returns:
            盘口数据
        """
        try:
            api = self._get_api()
            market = self._get_market_code(code)
            formatted_code = self._format_code(code)
            
            # 获取买卖盘口
            data = api.get_security_quotes([(market, formatted_code)])
            
            if not data or len(data) == 0:
                return None
            
            item = data[0]
            
            return {
                'code': code,
                'bid1': float(item['bid1']) if item.get('bid1') else None,
                'bid1_volume': int(item['bid_vol1']) if item.get('bid_vol1') else None,
                'bid2': float(item['bid2']) if item.get('bid2') else None,
                'bid2_volume': int(item['bid_vol2']) if item.get('bid_vol2') else None,
                'bid3': float(item['bid3']) if item.get('bid3') else None,
                'bid3_volume': int(item['bid_vol3']) if item.get('bid_vol3') else None,
                'bid4': float(item['bid4']) if item.get('bid4') else None,
                'bid4_volume': int(item['bid_vol4']) if item.get('bid_vol4') else None,
                'bid5': float(item['bid5']) if item.get('bid5') else None,
                'bid5_volume': int(item['bid_vol5']) if item.get('bid_vol5') else None,
                'ask1': float(item['ask1']) if item.get('ask1') else None,
                'ask1_volume': int(item['ask_vol1']) if item.get('ask_vol1') else None,
                'ask2': float(item['ask2']) if item.get('ask2') else None,
                'ask2_volume': int(item['ask_vol2']) if item.get('ask_vol2') else None,
                'ask3': float(item['ask3']) if item.get('ask3') else None,
                'ask3_volume': int(item['ask_vol3']) if item.get('ask_vol3') else None,
                'ask4': float(item['ask4']) if item.get('ask4') else None,
                'ask4_volume': int(item['ask_vol4']) if item.get('ask_vol4') else None,
                'ask5': float(item['ask5']) if item.get('ask5') else None,
                'ask5_volume': int(item['ask_vol5']) if item.get('ask_vol5') else None,
                'updated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"获取盘口数据失败 {code}: {e}")
            return None


# 全局服务实例
stock_service = StockDataService()
