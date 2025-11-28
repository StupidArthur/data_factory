"""
时间规律变化能力模板

支持基于时间的规律性变化，如：
- 光照强度随日出日落变化
- 温度随季节变化
- 周期性变化等
"""

import numpy as np
from typing import Dict, Any, Optional
from core.relationships.base import CapabilityTemplate


class TimePatternTemplate(CapabilityTemplate):
    """
    时间规律变化模板
    
    支持多种时间规律：
    - 正弦/余弦周期变化
    - 线性趋势
    - 指数趋势
    - 自定义函数
    
    Config格式：
    {
        'name': 'light_intensity',
        'output_name': 'F.light',
        'pattern_type': 'sinusoidal',  # 'sinusoidal', 'linear', 'exponential', 'custom'
        'amplitude': 100.0,            # 振幅（用于正弦）
        'period': 86400.0,             # 周期（秒，用于正弦）
        'phase': 0.0,                  # 相位（用于正弦）
        'offset': 50.0,                # 偏移量
        'trend': 0.001,                # 趋势系数（用于线性/指数）
        'noise_level': 0.05,           # 噪声水平（相对值）
    }
    """
    
    def validate_config(self):
        """验证配置"""
        pattern_type = self.config.get('pattern_type', 'sinusoidal')
        valid_types = ['sinusoidal', 'linear', 'exponential', 'custom']
        if pattern_type not in valid_types:
            raise ValueError(f"pattern_type必须是以下之一: {valid_types}")
        
        if pattern_type == 'sinusoidal':
            if 'amplitude' not in self.config:
                raise ValueError("正弦模式需要'amplitude'参数")
            if 'period' not in self.config:
                raise ValueError("正弦模式需要'period'参数")
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成时间规律数据
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 不使用
        
        Returns:
            生成的数据数组
        """
        pattern_type = self.config.get('pattern_type', 'sinusoidal')
        offset = self.config.get('offset', 0.0)
        noise_level = self.config.get('noise_level', 0.0)
        
        if pattern_type == 'sinusoidal':
            data = self._generate_sinusoidal(time_points)
        elif pattern_type == 'linear':
            data = self._generate_linear(time_points)
        elif pattern_type == 'exponential':
            data = self._generate_exponential(time_points)
        else:
            raise ValueError(f"不支持的模式类型: {pattern_type}")
        
        # 添加偏移
        data = data + offset
        
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, abs(data) * noise_level, size=len(data))
            data = data + noise
        
        return data
    
    def _generate_sinusoidal(self, time_points: np.ndarray) -> np.ndarray:
        """生成正弦周期数据"""
        amplitude = self.config.get('amplitude', 1.0)
        period = self.config.get('period', 86400.0)  # 默认24小时
        phase = self.config.get('phase', 0.0)
        
        # 转换为角度（弧度）
        angle = 2 * np.pi * (time_points - phase) / period
        data = amplitude * np.sin(angle)
        
        return data
    
    def _generate_linear(self, time_points: np.ndarray) -> np.ndarray:
        """生成线性趋势数据"""
        trend = self.config.get('trend', 0.0)
        # 相对于起始时间的线性变化
        time_offset = time_points - time_points[0]
        data = trend * time_offset
        return data
    
    def _generate_exponential(self, time_points: np.ndarray) -> np.ndarray:
        """生成指数趋势数据"""
        trend = self.config.get('trend', 0.0)
        time_offset = time_points - time_points[0]
        data = np.exp(trend * time_offset) - 1  # 减去1使得起始值为0
        return data

