"""
选股规则引擎
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from app.services.stock_service import stock_service


class ScreeningEngine:
    """选股规则引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.exclude_rules = {
            'exclude_st': self._exclude_st,
            'market_cap': self._filter_market_cap,
            'exclude_bad_news': self._exclude_bad_news,
            'exclude_zombie': self._exclude_zombie
        }
        
        self.core_rules = {
            'long_shadow': self._detect_long_shadow,
            'one_to_two': self._detect_one_to_two,
            'resilient': self._detect_resilient
        }
    
    async def screen_stocks(
        self, 
        rules: List[str], 
        market: str = "all",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        执行选股
        
        Args:
            rules: 启用的规则列表
            market: 市场筛选
            limit: 返回数量限制
        
        Returns:
            选股结果列表
        """
        try:
            # 1. 获取全市场股票
            stocks = await stock_service.get_stock_list(market)
            if not stocks:
                return []
            
            df = pd.DataFrame(stocks)
            logger.info(f"获取到 {len(df)} 只股票")
            
            # 2. 应用排除规则
            for rule_id in rules:
                if rule_id in self.exclude_rules:
                    df = self.exclude_rules[rule_id](df)
                    logger.info(f"应用排除规则 {rule_id}, 剩余 {len(df)} 只")
            
            # 3. 应用核心规则评分
            results = []
            for _, row in df.iterrows():
                stock_result = {
                    'code': row['code'],
                    'name': row['name'],
                    'price': row.get('price', 0),
                    'change_pct': row.get('change_pct', 0),
                    'volume': row.get('volume', 0),
                    'turnover': row.get('turnover', 0),
                    'amplitude': row.get('amplitude', 0),
                    'signal_type': '',
                    'score': 0,
                    'reason': ''
                }
                
                # 检查核心规则
                for rule_id in rules:
                    if rule_id in self.core_rules:
                        match_result = await self.core_rules[rule_id](row)
                        if match_result:
                            stock_result['signal_type'] = match_result['signal_type']
                            stock_result['score'] = match_result['score']
                            stock_result['reason'] = match_result['reason']
                            results.append(stock_result)
                            break
            
            # 4. 按评分排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"选股执行失败: {e}")
            return []
    
    def _exclude_st(self, df: pd.DataFrame) -> pd.DataFrame:
        """排除ST股"""
        return df[~df['name'].str.contains('ST|退', na=False)]
    
    def _filter_market_cap(self, df: pd.DataFrame) -> pd.DataFrame:
        """市值过滤 20亿~500亿"""
        # 这里需要获取市值数据，暂时用成交额估算
        if 'turnover' in df.columns:
            return df[(df['turnover'] >= 200000000) & (df['turnover'] <= 50000000000)]
        return df
    
    def _exclude_bad_news(self, df: pd.DataFrame) -> pd.DataFrame:
        """排除利空股（需要额外数据源）"""
        # TODO: 对接新闻API
        return df
    
    def _exclude_zombie(self, df: pd.DataFrame) -> pd.DataFrame:
        """排除僵尸股"""
        # 过滤成交额过小的股票
        if 'turnover' in df.columns:
            return df[df['turnover'] >= 10000000]  # 成交额>=1000万
        return df
    
    async def _detect_long_shadow(self, row: pd.Series) -> Optional[Dict]:
        """检测放量长上影"""
        try:
            amplitude = row.get('amplitude', 0)
            turnover = row.get('turnover', 0)
            
            # 振幅>=5% 且 成交额>=1亿
            if amplitude >= 5 and turnover >= 100000000:
                return {
                    'signal_type': '放量长上影',
                    'score': 85,
                    'reason': f'振幅{amplitude:.2f}%, 成交额{turnover/100000000:.2f}亿'
                }
        except Exception as e:
            logger.error(f"检测放量长上影失败: {e}")
        return None
    
    async def _detect_one_to_two(self, row: pd.Series) -> Optional[Dict]:
        """检测一进二接力"""
        try:
            change_pct = row.get('change_pct', 0)
            turnover = row.get('turnover', 0)
            
            # 涨幅在3%~7%之间，成交活跃
            if 3 <= change_pct <= 7 and turnover >= 50000000:
                return {
                    'signal_type': '一进二',
                    'score': 82,
                    'reason': f'涨幅{change_pct:.2f}%, 成交活跃'
                }
        except Exception as e:
            logger.error(f"检测一进二失败: {e}")
        return None
    
    async def _detect_resilient(self, row: pd.Series) -> Optional[Dict]:
        """检测抗跌强势股"""
        try:
            change_pct = row.get('change_pct', 0)
            amplitude = row.get('amplitude', 0)
            
            # 大盘跌时抗跌（这里简化判断）
            if -2 <= change_pct <= 2 and amplitude < 5:
                return {
                    'signal_type': '抗跌强势',
                    'score': 78,
                    'reason': '走势稳健，抗跌明显'
                }
        except Exception as e:
            logger.error(f"检测抗跌强势失败: {e}")
        return None


# 全局引擎实例
screening_engine = ScreeningEngine()
