"""
随机数生成能力模板

支持生成随机数数据，用于测试预测功能。
"""

import numpy as np
from typing import Dict, Any, Optional
from core.relationships.base import CapabilityTemplate


class RandomPatternTemplate(CapabilityTemplate):
    """
    随机数生成模板
    
    支持生成均匀分布或正态分布的随机数。
    
    Config格式：
    {
        'name': 'random_data',
        'output_name': 'F.random',
        'distribution': 'uniform',  # 'uniform', 'normal', 'constrained_random_walk'
        'min_value': -100.0,         # 最小值（用于均匀分布）
        'max_value': 100.0,          # 最大值（用于均匀分布）
        'mean': 0.0,                 # 均值（用于正态分布）
        'std': 50.0,                 # 标准差（用于正态分布）
        'step_range': [-3, 3],       # 步长范围（用于constrained_random_walk）
        'seed': None,                # 随机种子（可选，用于可重复性）
    }
    """
    
    def validate_config(self):
        """验证配置"""
        distribution = self.config.get('distribution', 'uniform')
        valid_distributions = ['uniform', 'normal', 'constrained_random_walk']
        if distribution not in valid_distributions:
            raise ValueError(f"distribution必须是以下之一: {valid_distributions}")
        
        if distribution == 'uniform':
            if 'min_value' not in self.config:
                raise ValueError("均匀分布需要'min_value'参数")
            if 'max_value' not in self.config:
                raise ValueError("均匀分布需要'max_value'参数")
            if self.config.get('min_value', 0) >= self.config.get('max_value', 0):
                raise ValueError("min_value必须小于max_value")
        
        elif distribution == 'normal':
            if 'mean' not in self.config:
                raise ValueError("正态分布需要'mean'参数")
            if 'std' not in self.config:
                raise ValueError("正态分布需要'std'参数")
        
        elif distribution == 'constrained_random_walk':
            if 'min_value' not in self.config:
                raise ValueError("约束随机游走需要'min_value'参数")
            if 'max_value' not in self.config:
                raise ValueError("约束随机游走需要'max_value'参数")
            if 'step_range' not in self.config:
                raise ValueError("约束随机游走需要'step_range'参数")
            if not isinstance(self.config.get('step_range'), (list, tuple)) or len(self.config.get('step_range', [])) != 2:
                raise ValueError("step_range必须是一个包含两个元素的列表或元组")
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成随机数数据
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 不使用
        
        Returns:
            生成的随机数数组
        """
        distribution = self.config.get('distribution', 'uniform')
        seed = self.config.get('seed', None)
        
        # 设置随机种子（如果提供）
        if seed is not None:
            np.random.seed(seed)
        
        if distribution == 'uniform':
            min_value = self.config.get('min_value', 0.0)
            max_value = self.config.get('max_value', 1.0)
            data = np.random.uniform(min_value, max_value, size=len(time_points))
        
        elif distribution == 'normal':
            mean = self.config.get('mean', 0.0)
            std = self.config.get('std', 1.0)
            data = np.random.normal(mean, std, size=len(time_points))
        
        elif distribution == 'constrained_random_walk':
            data = self._generate_constrained_random_walk(time_points)
        
        else:
            raise ValueError(f"不支持的分布类型: {distribution}")
        
        return data
    
    def _generate_constrained_random_walk(self, time_points: np.ndarray) -> np.ndarray:
        """
        生成约束随机游走数据
        
        每次变化量限制在step_range范围内，值限制在[min_value, max_value]范围内。
        
        Args:
            time_points: 时间点数组
        
        Returns:
            生成的随机游走数据数组
        """
        min_value = self.config.get('min_value', 0.0)
        max_value = self.config.get('max_value', 100.0)
        step_range = self.config.get('step_range', [-1.0, 1.0])
        seed = self.config.get('seed', None)
        
        if seed is not None:
            np.random.seed(seed)
        
        step_min, step_max = step_range[0], step_range[1]
        data = np.zeros_like(time_points, dtype=float)
        
        # 初始值设为范围内的随机值
        initial_value = np.random.uniform(min_value, max_value)
        data[0] = np.clip(initial_value, min_value, max_value)
        
        # 生成随机游走
        for i in range(1, len(data)):
            # 生成步长变化（在step_range范围内）
            step = np.random.uniform(step_min, step_max)
            # 计算新值
            new_value = data[i-1] + step
            # 限制在[min_value, max_value]范围内
            data[i] = np.clip(new_value, min_value, max_value)
        
        return data

