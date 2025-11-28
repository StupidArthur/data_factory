"""
多项式关系能力模板

支持多个数据之间的多项式关系，如：a = kx + ly + mz + n
"""

import numpy as np
from typing import Dict, Any, Optional, List
from core.relationships.base import CapabilityTemplate


class PolynomialTemplate(CapabilityTemplate):
    """
    多项式关系模板
    
    支持形式：output = c0 + c1*x1 + c2*x2 + ... + cn*xn + c12*x1*x2 + ...
    
    Config格式：
    {
        'name': 'combined_value',
        'output_name': 'F.combined',
        'source_names': ['F.x', 'F.y', 'F.z'],  # 源数据名称列表
        'coefficients': {
            'constant': 10.0,           # 常数项
            'F.x': 2.0,                 # x的系数
            'F.y': 3.0,                 # y的系数
            'F.z': 1.5,                 # z的系数
            'F.x*F.y': 0.1,             # 交叉项系数（可选）
        },
        'lag_seconds': 0,               # 滞后时间（秒），默认0（无滞后）
        'noise_level': 0.05,            # 噪声水平
    }
    """
    
    def validate_config(self):
        """验证配置"""
        if 'source_names' not in self.config:
            raise ValueError("多项式模板需要'source_names'参数")
        if not isinstance(self.config['source_names'], list):
            raise ValueError("'source_names'必须是一个列表")
        if len(self.config['source_names']) == 0:
            raise ValueError("'source_names'不能为空")
        
        if 'coefficients' not in self.config:
            raise ValueError("多项式模板需要'coefficients'参数")
        if not isinstance(self.config['coefficients'], dict):
            raise ValueError("'coefficients'必须是一个字典")
    
    def get_dependencies(self) -> list:
        """获取依赖的数据名称"""
        return self.config['source_names']
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成多项式关系数据
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 其他数据字典，必须包含所有source_names对应的数据
        
        Returns:
            生成的数据数组
        """
        if other_data is None:
            raise ValueError("多项式模板需要other_data参数")
        
        source_names = self.config['source_names']
        coefficients = self.config['coefficients']
        
        # 检查所有源数据是否存在
        for source_name in source_names:
            if source_name not in other_data:
                raise ValueError(f"缺少依赖数据: {source_name}")
        
        # 获取滞后参数
        lag_seconds = self.config.get('lag_seconds', 0)
        
        # 计算滞后点数
        time_interval = time_points[1] - time_points[0] if len(time_points) > 1 else 5.0
        lag_points = int(round(lag_seconds / time_interval)) if lag_seconds > 0 else 0
        
        # 初始化输出数据
        data = np.zeros_like(time_points, dtype=float)
        
        # 添加常数项
        constant = coefficients.get('constant', 0.0)
        data[:] = constant
        
        # 添加线性项和交叉项（考虑滞后）
        for i in range(len(data)):
            # 计算滞后后的源数据索引
            source_idx = i - lag_points if lag_points > 0 else i
            
            if source_idx < 0:
                # 如果滞后索引小于0，使用源数据的第一个值
                source_idx = 0
            
            # 添加线性项
            for source_name in source_names:
                if source_name in coefficients:
                    coeff = coefficients[source_name]
                    source_data = other_data[source_name]
                    data[i] += coeff * source_data[source_idx]
            
            # 添加交叉项（如果存在）
            for term, coeff in coefficients.items():
                if '*' in term:
                    # 解析交叉项，如 'F.x*F.y'
                    factors = [f.strip() for f in term.split('*')]
                    if all(f in other_data for f in factors):
                        product = 1.0
                        for factor in factors:
                            product *= other_data[factor][source_idx]
                        data[i] += coeff * product
        
        # 添加噪声
        noise_level = self.config.get('noise_level', 0.0)
        if noise_level > 0:
            noise = np.random.normal(0, abs(data) * noise_level, size=len(data))
            data = data + noise
        
        return data

