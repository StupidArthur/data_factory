"""
滞后线性跟随能力模板

支持一个数据跟随另一个数据的变化，但存在时间滞后。
例如：热水器的水温会随着电功率呈现滞后的上涨。
"""

import numpy as np
from typing import Dict, Any, Optional
from core.relationships.base import CapabilityTemplate


class LagFollowTemplate(CapabilityTemplate):
    """
    滞后线性跟随模板
    
    Config格式：
    {
        'name': 'water_temperature',
        'output_name': 'F.temperature',
        'source_name': 'F.power',        # 跟随的数据名称
        'lag_seconds': 30,               # 滞后时间（秒）
        'sensitivity': 0.5,              # 敏感度系数（跟随强度）
        'initial_value': 20.0,           # 初始值
        'decay_rate': 0.01,              # 衰减率（当源数据不变时的衰减速度）
        'noise_level': 0.02,             # 噪声水平
    }
    """
    
    def validate_config(self):
        """验证配置"""
        if 'source_name' not in self.config:
            raise ValueError("滞后跟随模板需要'source_name'参数")
        if 'lag_seconds' not in self.config:
            raise ValueError("滞后跟随模板需要'lag_seconds'参数")
        if self.config.get('lag_seconds', 0) < 0:
            raise ValueError("lag_seconds必须大于等于0")
    
    def get_dependencies(self) -> list:
        """获取依赖的数据名称"""
        return [self.config['source_name']]
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成滞后跟随数据
        
        实现逻辑：value2[t] = value1[t - delay] * sensitivity + offset
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 其他数据字典，必须包含source_name对应的数据
        
        Returns:
            生成的数据数组
        """
        if other_data is None:
            raise ValueError("滞后跟随模板需要other_data参数")
        
        source_name = self.config['source_name']
        if source_name not in other_data:
            raise ValueError(f"缺少依赖数据: {source_name}")
        
        source_data = other_data[source_name]
        lag_seconds = self.config.get('lag_seconds', 0)
        sensitivity = self.config.get('sensitivity', 1.0)
        initial_value = self.config.get('initial_value', 0.0)
        decay_rate = self.config.get('decay_rate', 0.0)
        noise_level = self.config.get('noise_level', 0.0)
        
        # 计算滞后点数
        # 确保time_points和source_data长度一致
        if len(time_points) != len(source_data):
            raise ValueError(f"time_points长度({len(time_points)})与source_data长度({len(source_data)})不一致")
        
        time_interval = time_points[1] - time_points[0] if len(time_points) > 1 else 5.0
        lag_points = int(round(lag_seconds / time_interval))  # 使用round确保精确计算
        
        # 验证滞后点数计算
        actual_lag_time = lag_points * time_interval
        if abs(actual_lag_time - lag_seconds) > 0.1:
            # 如果计算误差较大，发出警告
            import warnings
            warnings.warn(f"滞后点数计算可能有误差: lag_points={lag_points}, "
                         f"实际滞后时间={actual_lag_time}秒, "
                         f"期望滞后时间={lag_seconds}秒")
        
        # 调试信息：打印关键参数
        from utils.logger import get_logger
        logger = get_logger()
        logger.debug(f"滞后跟随计算: lag_seconds={lag_seconds}, time_interval={time_interval}, "
                    f"lag_points={lag_points}, 实际滞后时间={actual_lag_time}秒")
        
        # 初始化输出数据
        data = np.zeros_like(time_points, dtype=float)
        
        # 生成滞后跟随数据：value2[i] = value1[i - lag_points]
        # 例如：lag_points=60时，value2[60] = value1[0], value2[61] = value1[1], ...
        # 对于前lag_points个点，由于source_idx < 0，使用源数据的第一个值（而不是initial_value）
        # 这样可以确保value2从一开始就跟随value1，只是滞后lag_points个点
        for i in range(len(data)):
            # 计算滞后后的源数据索引
            source_idx = i - lag_points
            
            if source_idx < 0:
                # 如果滞后索引小于0，使用源数据的第一个值（而不是initial_value）
                # 这样可以保持数据的连续性
                # 例如：i=0到59时，source_idx=-60到-1，使用source_data[0]
                data[i] = source_data[0] * sensitivity
            else:
                # 直接使用滞后后的源数据值
                # 例如：i=60时，source_idx=0，data[60] = source_data[0]
                lagged_value = source_data[source_idx]
                # 应用敏感度
                data[i] = lagged_value * sensitivity
                
                # 应用衰减（如果启用）
                if decay_rate > 0 and i > 0:
                    decay = -decay_rate * (data[i-1] - initial_value)
                    data[i] = data[i] + decay
        
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, abs(data) * noise_level, size=len(data))
            data = data + noise
        
        return data

