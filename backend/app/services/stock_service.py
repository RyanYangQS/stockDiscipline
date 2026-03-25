"""
股票数据服务 - 对接AKShare
"""
import akshare as ak
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from app.core.config import settings
import os
import requests


class StockDataService:
    """股票数据服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.cache = {}
        self.cache_timeout = 300  # 缓存5分钟
        self.use_fallback = True  # 开发模式默认使用模拟数据，避免网络超时
    
    async def get_stock_list(self, market: str = "all") -> List[Dict[str, Any]]:
        """
        获取股票列表
        
        Args:
            market: 市场筛选 all/sh/sz
        
        Returns:
            股票列表
        """
        # 开发模式直接使用模拟数据，避免网络超时
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟股票列表 {market}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_stock_list(market)
        
        try:
            # 获取A股股票列表
            df = ak.stock_zh_a_spot_em()
            
            # 数据清洗
            df = df.rename(columns={
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'turnover',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close'
            })
            
            # 市场筛选
            if market == "sh":
                df = df[df['code'].str.startswith(('60', '68'))]
            elif market == "sz":
                df = df[df['code'].str.startswith(('00', '30'))]
            
            # 转换为字典列表
            stocks = df.to_dict('records')
            logger.info(f"从AkShare获取股票列表成功: {len(stocks)}条")
            return stocks
            
        except Exception as e:
            logger.warning(f"从AkShare获取股票列表失败: {e}, 使用模拟数据")
            # 使用模拟数据
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
        # 开发模式直接使用模拟数据，避免网络超时
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟实时行情 {code}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_realtime_quote(code)
        
        try:
            df = ak.stock_zh_a_spot_em()
            stock = df[df['代码'] == code]
            
            if stock.empty:
                return None
            
            return {
                'code': code,
                'name': stock['名称'].values[0],
                'price': float(stock['最新价'].values[0]),
                'change_pct': float(stock['涨跌幅'].values[0]),
                'change': float(stock['涨跌额'].values[0]),
                'volume': int(stock['成交量'].values[0]),
                'turnover': float(stock['成交额'].values[0]),
                'amplitude': float(stock['振幅'].values[0]),
                'high': float(stock['最高'].values[0]),
                'low': float(stock['最低'].values[0]),
                'open': float(stock['今开'].values[0]),
                'pre_close': float(stock['昨收'].values[0])
            }
        except Exception as e:
            logger.warning(f"从AkShare获取实时行情失败 {code}: {e}, 使用模拟数据")
            # 使用模拟数据
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
        # 开发模式直接使用模拟数据，避免网络超时
        if self.use_fallback:
            logger.info(f"开发模式: 使用模拟K线数据 {code}")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_kline_data(code, count)
        
        try:
            # 尝试从AkShare获取数据
            if period == "weekly":
                df = ak.stock_zh_a_hist(symbol=code, period="weekly", adjust="qfq")
            else:
                df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            
            df = df.tail(count)
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'turnover',
            })
            
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    'timestamp': pd.to_datetime(row['date']).to_pydatetime(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'turnover': float(row['turnover']) if 'turnover' in row else None,
                })
            
            logger.info(f"从AkShare获取K线数据成功: {code}, {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.warning(f"从AkShare获取K线数据失败 {code}: {e}, 使用模拟数据")
            
            # 使用模拟数据（测试用）
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_kline_data(code, count)
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览
        
        Returns:
            市场概览数据
        """
        # 开发模式直接使用模拟数据
        if self.use_fallback:
            logger.info("开发模式: 使用模拟市场概览")
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_market_overview()
        
        try:
            df = ak.stock_zh_a_spot_em()
            
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])
            limit_up_count = len(df[df['涨跌幅'] >= 9.9])
            limit_down_count = len(df[df['涨跌幅'] <= -9.9])
            
            logger.info(f"从AkShare获取市场概览成功")
            return {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'total_count': len(df),
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'updated_at': datetime.now()
            }
        except Exception as e:
            logger.warning(f"从AkShare获取市场概览失败: {e}, 使用模拟数据")
            # 使用模拟数据
            from app.services.data_fallback import DataFallbackService
            return DataFallbackService.generate_market_overview()
    
    async def get_stock_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票详细信息
        
        Args:
            code: 股票代码
        
        Returns:
            股票信息
        """
        try:
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=code)
            
            info = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            
            return {
                'code': code,
                'name': info.get('股票简称', ''),
                'industry': info.get('行业', ''),
                'market_cap': float(info.get('流通市值', 0)) / 100000000 if '流通市值' in info else None,
                'is_st': 'ST' in info.get('股票简称', '') or '*' in info.get('股票简称', '')
            }
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
            # 获取实时盘口数据
            df = ak.stock_bid_ask_em(symbol=code)
            
            # 转换为字典
            bid_ask = {}
            for _, row in df.iterrows():
                bid_ask[row['item']] = row['value']
            
            # 解析买卖五档
            result = {
                'code': code,
                'bid1': float(bid_ask.get('买一', 0)) if bid_ask.get('买一') else None,
                'bid1_volume': int(bid_ask.get('买量一', 0)) if bid_ask.get('买量一') else None,
                'bid2': float(bid_ask.get('买二', 0)) if bid_ask.get('买二') else None,
                'bid2_volume': int(bid_ask.get('买量二', 0)) if bid_ask.get('买量二') else None,
                'bid3': float(bid_ask.get('买三', 0)) if bid_ask.get('买三') else None,
                'bid3_volume': int(bid_ask.get('买量三', 0)) if bid_ask.get('买量三') else None,
                'bid4': float(bid_ask.get('买四', 0)) if bid_ask.get('买四') else None,
                'bid4_volume': int(bid_ask.get('买量四', 0)) if bid_ask.get('买量四') else None,
                'bid5': float(bid_ask.get('买五', 0)) if bid_ask.get('买五') else None,
                'bid5_volume': int(bid_ask.get('买量五', 0)) if bid_ask.get('买量五') else None,
                'ask1': float(bid_ask.get('卖一', 0)) if bid_ask.get('卖一') else None,
                'ask1_volume': int(bid_ask.get('卖量一', 0)) if bid_ask.get('卖量一') else None,
                'ask2': float(bid_ask.get('卖二', 0)) if bid_ask.get('卖二') else None,
                'ask2_volume': int(bid_ask.get('卖量二', 0)) if bid_ask.get('卖量二') else None,
                'ask3': float(bid_ask.get('卖三', 0)) if bid_ask.get('卖三') else None,
                'ask3_volume': int(bid_ask.get('卖量三', 0)) if bid_ask.get('卖量三') else None,
                'ask4': float(bid_ask.get('卖四', 0)) if bid_ask.get('卖四') else None,
                'ask4_volume': int(bid_ask.get('卖量四', 0)) if bid_ask.get('卖量四') else None,
                'ask5': float(bid_ask.get('卖五', 0)) if bid_ask.get('卖五') else None,
                'ask5_volume': int(bid_ask.get('卖量五', 0)) if bid_ask.get('卖量五') else None,
                'updated_at': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取盘口数据失败 {code}: {e}")
            return None
    
    async def get_intraday_data(self, code: str) -> List[Dict[str, Any]]:
        """
        获取分时数据
        
        Args:
            code: 股票代码
        
        Returns:
            分时数据列表
        """
        try:
            # 获取分时数据
            df = ak.stock_zh_a_minute(symbol=code, period='1', adjust="qfq")
            
            # 只取当天的数据
            today = datetime.now().date()
            df['day'] = pd.to_datetime(df['day'])
            df = df[df['day'].dt.date == today]
            
            # 转换为字典列表
            intraday = []
            for _, row in df.iterrows():
                intraday.append({
                    'timestamp': pd.to_datetime(row['day']).to_pydatetime(),
                    'price': float(row['close']),
                    'volume': int(row['volume']),
                    'avg_price': float(row.get('avg_price', 0)) if 'avg_price' in row else None
                })
            
            return intraday
            
        except Exception as e:
            logger.error(f"获取分时数据失败 {code}: {e}")
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
        try:
            # 获取分钟K线数据
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period, adjust="qfq")
            
            # 取最近count条数据
            df = df.tail(count)
            
            # 数据清洗
            df = df.rename(columns={
                '时间': 'time',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'turnover'
            })
            
            # 转换为字典列表
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    'timestamp': pd.to_datetime(row['time']).to_pydatetime(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'turnover': float(row['turnover']) if 'turnover' in row else None
                })
            
            return klines
            
        except Exception as e:
            logger.error(f"获取分钟K线数据失败 {code}: {e}")
            return []


# 全局服务实例
stock_service = StockDataService()
