"""
风控规则引擎
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from app.core.config import settings


class RiskEngine:
    """
    风控规则引擎
    
    管理止损止盈、仓位控制、风险预警
    """
    
    # 默认风控参数
    DEFAULT_PARAMS = {
        'max_stop_loss_pct': 8.0,        # 最大止损比例
        'take_profit_l1': 3.0,           # 止盈阶梯1
        'take_profit_l2': 5.0,           # 止盈阶梯2
        'take_profit_l3': 10.0,          # 止盈阶梯3（移动止盈触发点）
        'max_position_ratio': 0.8,       # 最大总仓位
        'single_position_ratio': 0.3,    # 单股最大仓位
        'consecutive_loss_limit': 3,     # 连续亏损天数限制
        'consecutive_loss_position': 0.3, # 连续亏损后限仓比例
        'max_daily_drawdown': 5.0,       # 单日最大回撤
        'max_total_drawdown': 15.0       # 总最大回撤
    }
    
    def __init__(self):
        """初始化风控引擎"""
        self.params = self.DEFAULT_PARAMS.copy()
    
    def update_params(self, new_params: Dict[str, Any]):
        """
        更新风控参数
        
        Args:
            new_params: 新参数字典
        """
        self.params.update(new_params)
        logger.info(f"风控参数已更新: {new_params}")
    
    def calculate_stop_loss_price(self, cost_price: float) -> float:
        """
        计算止损价
        
        Args:
            cost_price: 成本价
        
        Returns:
            止损价
        """
        return cost_price * (1 - self.params['max_stop_loss_pct'] / 100)
    
    def calculate_take_profit_prices(self, cost_price: float) -> Dict[str, float]:
        """
        计算止盈价阶梯
        
        Args:
            cost_price: 成本价
        
        Returns:
            各级止盈价
        """
        return {
            'l1': cost_price * (1 + self.params['take_profit_l1'] / 100),
            'l2': cost_price * (1 + self.params['take_profit_l2'] / 100),
            'l3': cost_price * (1 + self.params['take_profit_l3'] / 100)
        }
    
    def check_can_open_position(
        self,
        account_balance: float,
        current_positions: List[Dict],
        daily_pnl: float = 0,
        consecutive_loss_days: int = 0
    ) -> Dict[str, Any]:
        """
        检查是否可以开仓
        
        Args:
            account_balance: 账户余额
            current_positions: 当前持仓列表
            daily_pnl: 当日盈亏
            consecutive_loss_days: 连续亏损天数
        
        Returns:
            检查结果
        """
        result = {
            'can_open': True,
            'max_position_ratio': self.params['max_position_ratio'],
            'reason': ''
        }
        
        # 计算当前总仓位
        total_position_value = sum(p.get('market_value', 0) for p in current_positions)
        current_ratio = total_position_value / account_balance if account_balance > 0 else 0
        
        # 检查总仓位限制
        if current_ratio >= self.params['max_position_ratio']:
            result['can_open'] = False
            result['reason'] = f'总仓位已达{current_ratio*100:.1f}%，超过上限{self.params["max_position_ratio"]*100}%'
            return result
        
        # 检查持仓数量
        if len(current_positions) >= 5:
            result['can_open'] = False
            result['reason'] = '持仓数量已达上限5只'
            return result
        
        # 检查连续亏损限仓
        if consecutive_loss_days >= self.params['consecutive_loss_limit']:
            result['max_position_ratio'] = self.params['consecutive_loss_position']
            if current_ratio >= self.params['consecutive_loss_position']:
                result['can_open'] = False
                result['reason'] = f'连续亏损{consecutive_loss_days}天，仓位限制为{self.params["consecutive_loss_position"]*100}%'
        
        # 检查单日回撤
        if daily_pnl < 0:
            daily_drawdown = abs(daily_pnl) / account_balance * 100
            if daily_drawdown >= self.params['max_daily_drawdown']:
                result['can_open'] = False
                result['reason'] = f'当日回撤{daily_drawdown:.1f}%，超过限制{self.params["max_daily_drawdown"]}%'
        
        return result
    
    def check_position_risk(
        self,
        position: Dict,
        current_price: float
    ) -> Dict[str, Any]:
        """
        检查单个持仓风险
        
        Args:
            position: 持仓信息
            current_price: 当前价格
        
        Returns:
            风险检查结果
        """
        cost_price = position.get('cost_price', 0)
        quantity = position.get('quantity', 0)
        
        if cost_price <= 0:
            return {'risk_level': 'unknown', 'alerts': []}
        
        profit_pct = (current_price - cost_price) / cost_price * 100
        profit = (current_price - cost_price) * quantity
        
        alerts = []
        risk_level = 'low'
        
        # 止损检查
        stop_loss_price = self.calculate_stop_loss_price(cost_price)
        if current_price <= stop_loss_price:
            alerts.append({
                'type': 'stop_loss',
                'level': 'critical',
                'message': f'触发止损！当前价{current_price:.2f}，止损价{stop_loss_price:.2f}'
            })
            risk_level = 'critical'
        elif profit_pct <= -5:
            alerts.append({
                'type': 'stop_loss_warning',
                'level': 'high',
                'message': f'接近止损线！当前亏损{abs(profit_pct):.2f}%'
            })
            risk_level = 'high'
        
        # 止盈检查
        take_profit_prices = self.calculate_take_profit_prices(cost_price)
        
        if profit_pct >= self.params['take_profit_l3']:
            alerts.append({
                'type': 'trailing_stop',
                'level': 'medium',
                'message': f'建议设置移动止盈，当前盈利{profit_pct:.2f}%'
            })
        elif profit_pct >= self.params['take_profit_l2']:
            alerts.append({
                'type': 'take_profit_l2',
                'level': 'medium',
                'message': f'达到二级止盈点，可考虑部分止盈'
            })
        elif profit_pct >= self.params['take_profit_l1']:
            alerts.append({
                'type': 'take_profit_l1',
                'level': 'low',
                'message': f'达到一级止盈提醒，当前盈利{profit_pct:.2f}%'
            })
        
        return {
            'risk_level': risk_level,
            'profit': profit,
            'profit_pct': profit_pct,
            'stop_loss_price': stop_loss_price,
            'take_profit_prices': take_profit_prices,
            'alerts': alerts
        }
    
    def calculate_position_size(
        self,
        account_balance: float,
        stock_price: float,
        risk_per_trade: float = 0.02
    ) -> int:
        """
        计算建议仓位大小
        
        Args:
            account_balance: 账户余额
            stock_price: 股票价格
            risk_per_trade: 单笔风险比例（默认2%）
        
        Returns:
            建议买入数量
        """
        # 单笔最大风险金额
        max_risk_amount = account_balance * risk_per_trade
        
        # 止损幅度
        stop_loss_pct = self.params['max_stop_loss_pct'] / 100
        
        # 每股最大风险
        risk_per_share = stock_price * stop_loss_pct
        
        # 计算数量
        if risk_per_share > 0:
            quantity = int(max_risk_amount / risk_per_share)
        else:
            quantity = 0
        
        # 单股仓位限制
        max_position_value = account_balance * self.params['single_position_ratio']
        max_quantity = int(max_position_value / stock_price)
        
        return min(quantity, max_quantity)
    
    def get_trading_status(
        self,
        positions: List[Dict],
        account_balance: float,
        daily_pnl: float = 0,
        consecutive_loss_days: int = 0
    ) -> Dict[str, Any]:
        """
        获取交易状态概览
        
        Args:
            positions: 持仓列表
            account_balance: 账户余额
            daily_pnl: 当日盈亏
            consecutive_loss_days: 连续亏损天数
        
        Returns:
            交易状态
        """
        total_position_value = sum(p.get('market_value', 0) for p in positions)
        total_profit = sum(p.get('profit', 0) for p in positions)
        
        position_ratio = total_position_value / account_balance if account_balance > 0 else 0
        daily_pnl_pct = daily_pnl / account_balance * 100 if account_balance > 0 else 0
        
        # 确定交易状态
        if consecutive_loss_days >= self.params['consecutive_loss_limit']:
            status = 'restricted'
            status_text = f'连续亏损{consecutive_loss_days}天，限仓{self.params["consecutive_loss_position"]*100}%'
        elif abs(daily_pnl_pct) >= self.params['max_daily_drawdown']:
            status = 'warning'
            status_text = f'当日回撤{abs(daily_pnl_pct):.1f}%，注意风险'
        elif position_ratio >= self.params['max_position_ratio']:
            status = 'full'
            status_text = '仓位已满'
        else:
            status = 'normal'
            status_text = '正常交易'
        
        return {
            'status': status,
            'status_text': status_text,
            'position_count': len(positions),
            'position_ratio': position_ratio,
            'total_position_value': total_position_value,
            'total_profit': total_profit,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'consecutive_loss_days': consecutive_loss_days,
            'can_open_count': max(0, 5 - len(positions))
        }


# 全局风控引擎实例
risk_engine = RiskEngine()
