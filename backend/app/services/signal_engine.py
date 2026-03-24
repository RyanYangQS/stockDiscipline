"""
买卖信号引擎
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from app.services.stock_service import stock_service


class SignalEngine:
    """
    买卖信号引擎
    
    根据交易规则生成买入/卖出信号建议
    """
    
    def __init__(self):
        """初始化信号引擎"""
        self.buy_rules = {
            'volume_shrink_stable': self._detect_volume_shrink_stable,
            'weak_to_strong': self._detect_weak_to_strong,
            'late_confirm': self._detect_late_confirm,
            'board_buy': self._detect_board_buy
        }
        
        self.sell_rules = {
            'stop_loss': self._detect_stop_loss,
            'take_profit': self._detect_take_profit,
            'break_down': self._detect_break_down
        }
    
    async def analyze_signals(
        self, 
        code: str, 
        kline_data: List[Dict],
        position: Optional[Dict] = None
    ) -> Dict[str, List[Dict]]:
        """
        分析股票信号
        
        Args:
            code: 股票代码
            kline_data: K线数据
            position: 持仓信息（可选）
        
        Returns:
            买入信号和卖出信号
        """
        if not kline_data or len(kline_data) < 20:
            return {'buy': [], 'sell': [], 'warn': []}
        
        df = pd.DataFrame(kline_data)
        df['date'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('date')
        
        # 计算技术指标
        df = self._calc_indicators(df)
        
        buy_signals = []
        sell_signals = []
        warn_signals = []
        
        # 检测买入信号
        for rule_name, rule_func in self.buy_rules.items():
            try:
                signal = await rule_func(df, code)
                if signal:
                    buy_signals.append(signal)
            except Exception as e:
                logger.error(f"检测买入信号失败 {rule_name}: {e}")
        
        # 如果有持仓，检测卖出信号
        if position:
            for rule_name, rule_func in self.sell_rules.items():
                try:
                    signal = await rule_func(df, position, code)
                    if signal:
                        sell_signals.append(signal)
                except Exception as e:
                    logger.error(f"检测卖出信号失败 {rule_name}: {e}")
            
            # 风控预警
            warn_signals.extend(self._check_risk_warnings(df, position))
        
        return {
            'buy': buy_signals,
            'sell': sell_signals,
            'warn': warn_signals
        }
    
    def _calc_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: K线数据DataFrame
        
        Returns:
            添加指标后的DataFrame
        """
        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # 成交量均线
        df['vol_ma5'] = df['volume'].rolling(window=5).mean()
        df['vol_ma10'] = df['volume'].rolling(window=10).mean()
        df['vol_ma20'] = df['volume'].rolling(window=20).mean()
        
        # 振幅
        df['amplitude'] = (df['high'] - df['low']) / df['pre_close'] * 100
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        
        # 涨跌幅
        df['change_pct'] = (df['close'] - df['pre_close']) / df['pre_close'] * 100
        
        # 量比
        df['volume_ratio'] = df['volume'] / df['vol_ma5']
        
        # 换手率（需要流通股本数据，这里简化处理）
        # df['turnover_rate'] = df['volume'] / df['float_shares'] * 100
        
        return df
    
    async def _detect_volume_shrink_stable(self, df: pd.DataFrame, code: str) -> Optional[Dict]:
        """
        检测缩量企稳买入信号
        
        条件:
        1. 回调缩量25%以上
        2. 在均价线(MA20)附近企稳
        3. 收盘价站稳均价线
        """
        if len(df) < 30:
            return None
        
        recent = df.iloc[-1]
        prev = df.iloc[-2:-6]  # 前5日数据
        
        # 量能萎缩
        avg_volume = prev['volume'].mean()
        if recent['volume'] < avg_volume * 0.75:  # 缩量25%
            # 价格在MA20附近
            if abs(recent['close'] - recent['ma20']) / recent['ma20'] < 0.03:
                # 收盘价站稳均价线
                if recent['close'] > recent['ma20']:
                    return {
                        'stock_code': code,
                        'signal_type': 'buy',
                        'signal_name': '缩量企稳买入',
                        'price': float(recent['close']),
                        'priority': 'HIGH',
                        'reason': f'回调缩量{(1 - recent["volume"]/avg_volume)*100:.1f}%，均价线支撑有效'
                    }
        return None
    
    async def _detect_weak_to_strong(self, df: pd.DataFrame, code: str) -> Optional[Dict]:
        """
        检测弱转强买入信号
        
        条件:
        1. MA5上穿MA10
        2. 成交量放大
        3. 收盘价站上MA5
        """
        if len(df) < 15:
            return None
        
        recent = df.iloc[-1]
        prev = df.iloc[-2]
        
        # MA5上穿MA10
        if prev['ma5'] <= prev['ma10'] and recent['ma5'] > recent['ma10']:
            # 成交量放大
            if recent['volume'] > prev['volume'] * 1.2:
                # 收盘价站上MA5
                if recent['close'] > recent['ma5']:
                    return {
                        'stock_code': code,
                        'signal_type': 'buy',
                        'signal_name': '弱转强买入',
                        'price': float(recent['close']),
                        'priority': 'MEDIUM',
                        'reason': 'MA5上穿MA10，成交量放大，走势转强'
                    }
        return None
    
    async def _detect_late_confirm(self, df: pd.DataFrame, code: str) -> Optional[Dict]:
        """
        检测尾盘确定性买入信号
        
        条件（简化处理，实际需要分时数据）:
        1. 日内涨幅在3%-7%之间
        2. 收盘价接近当日最高价
        3. 成交量适中
        """
        recent = df.iloc[-1]
        
        # 日内涨幅3%-7%
        if 3 <= recent['change_pct'] <= 7:
            # 收盘价接近最高价（上影线短）
            upper_shadow_ratio = recent['upper_shadow'] / (recent['high'] - recent['low']) if recent['high'] != recent['low'] else 0
            if upper_shadow_ratio < 0.3:  # 上影线占比小于30%
                return {
                    'stock_code': code,
                    'signal_type': 'buy',
                    'signal_name': '尾盘确定性买入',
                    'price': float(recent['close']),
                    'priority': 'MEDIUM',
                    'reason': f"涨幅{recent['change_pct']:.2f}%，上影线短，走势稳健"
                }
        return None
    
    async def _detect_board_buy(self, df: pd.DataFrame, code: str) -> Optional[Dict]:
        """
        检测打板买入信号
        
        条件:
        1. 涨幅接近10%（或20%/30%）
        2. 封板迹象（收盘价=最高价=涨停价）
        """
        recent = df.iloc[-1]
        
        # 涨幅接近涨停
        if recent['change_pct'] >= 9.5:
            # 收盘价等于最高价，表示封板
            if abs(recent['close'] - recent['high']) < 0.01:
                return {
                    'stock_code': code,
                    'signal_type': 'buy',
                    'signal_name': '打板买入',
                    'price': float(recent['close']),
                    'priority': 'HIGH',
                    'reason': f"涨停封板，涨幅{recent['change_pct']:.2f}%"
                }
        return None
    
    async def _detect_stop_loss(self, df: pd.DataFrame, position: Dict, code: str) -> Optional[Dict]:
        """
        检测止损卖出信号
        
        条件:
        亏损达到止损线(8%)
        """
        recent = df.iloc[-1]
        cost_price = position.get('cost_price', 0)
        
        if cost_price > 0:
            loss_pct = (recent['close'] - cost_price) / cost_price * 100
            
            if loss_pct <= -8:
                return {
                    'stock_code': code,
                    'signal_type': 'sell',
                    'signal_name': '止损提醒',
                    'price': float(recent['close']),
                    'priority': 'HIGH',
                    'reason': f'触发8%硬止损，当前亏损{abs(loss_pct):.2f}%'
                }
        return None
    
    async def _detect_take_profit(self, df: pd.DataFrame, position: Dict, code: str) -> Optional[Dict]:
        """
        检测止盈卖出信号
        
        条件:
        盈利达到止盈阶梯
        """
        recent = df.iloc[-1]
        cost_price = position.get('cost_price', 0)
        
        if cost_price > 0:
            profit_pct = (recent['close'] - cost_price) / cost_price * 100
            
            # 阶梯止盈
            if profit_pct >= 10:
                return {
                    'stock_code': code,
                    'signal_type': 'sell',
                    'signal_name': '移动止盈',
                    'price': float(recent['close']),
                    'priority': 'MEDIUM',
                    'reason': f'浮盈{profit_pct:.2f}%，建议设置移动止盈'
                }
            elif profit_pct >= 5:
                return {
                    'stock_code': code,
                    'signal_type': 'sell',
                    'signal_name': '阶梯止盈',
                    'price': float(recent['close']),
                    'priority': 'LOW',
                    'reason': f'浮盈{profit_pct:.2f}%，可考虑部分止盈'
                }
        return None
    
    async def _detect_break_down(self, df: pd.DataFrame, position: Dict, code: str) -> Optional[Dict]:
        """
        检测破位卖出信号
        
        条件:
        1. 三根K线逐级降低
        2. 跌破均价线
        """
        if len(df) < 5:
            return None
        
        recent = df.iloc[-3:]
        
        # 三根K线逐级降低
        if (recent.iloc[0]['close'] > recent.iloc[1]['close'] > recent.iloc[2]['close']):
            # 跌破MA20
            if recent.iloc[2]['close'] < recent.iloc[2]['ma20']:
                return {
                    'stock_code': code,
                    'signal_type': 'sell',
                    'signal_name': '破位卖出',
                    'price': float(recent.iloc[2]['close']),
                    'priority': 'HIGH',
                    'reason': '三根K线逐级降低，跌破均价线'
                }
        return None
    
    def _check_risk_warnings(self, df: pd.DataFrame, position: Dict) -> List[Dict]:
        """
        检查风控预警
        
        Args:
            df: K线数据
            position: 持仓信息
        
        Returns:
            预警信号列表
        """
        warnings = []
        recent = df.iloc[-1]
        cost_price = position.get('cost_price', 0)
        
        if cost_price > 0:
            profit_pct = (recent['close'] - cost_price) / cost_price * 100
            
            # 盈亏预警
            if profit_pct >= 3:
                warnings.append({
                    'stock_code': position.get('stock_code'),
                    'signal_type': 'warn',
                    'signal_name': '阶梯止盈',
                    'price': float(recent['close']),
                    'priority': 'LOW',
                    'reason': f'浮盈达{profit_pct:.2f}%，建议设置止盈'
                })
            
            # 亏损预警
            if profit_pct <= -5:
                warnings.append({
                    'stock_code': position.get('stock_code'),
                    'signal_type': 'warn',
                    'signal_name': '亏损预警',
                    'price': float(recent['close']),
                    'priority': 'HIGH',
                    'reason': f'当前亏损{abs(profit_pct):.2f}%，接近止损线'
                })
        
        return warnings


# 全局引擎实例
signal_engine = SignalEngine()
