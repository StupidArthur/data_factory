"""
非线性滞后关系能力模板

支持多个数据之间的非线性关系，并支持滞后。
例如：value3[index] = sqrt(value1[index - 60] * value2[index - 60])
"""

import numpy as np
from typing import Dict, Any, Optional, List
from core.relationships.base import CapabilityTemplate


class NonlinearLagTemplate(CapabilityTemplate):
    """
    非线性滞后关系模板
    
    支持形式：output[i] = function(source1[i - lag], source2[i - lag], ...)
    
    Config格式：
    {
        'output_name': 'F.value3',
        'source_names': ['F.value1', 'F.value2'],  # 源数据名称列表
        'function': 'sqrt',                         # 函数类型：'sqrt', 'log', 'exp', 'power', 'custom'
        'function_params': {},                      # 函数参数（可选）
        'lag_seconds': 300,                        # 滞后时间（秒）
        'noise_level': 0.0,                        # 噪声水平
    }
    
    支持的函数：
    - 'sqrt': sqrt(x1 * x2 * ...) 或 sqrt(x1 + x2 + ...)
    - 'log': log(x1 + x2 + ...)
    - 'exp': exp(x1 + x2 + ...)
    - 'power': (x1 + x2 + ...)^n
    - 'custom': 自定义表达式（需要提供function_expr）
    """
    
    def validate_config(self):
        """验证配置"""
        if 'source_names' not in self.config:
            raise ValueError("非线性滞后模板需要'source_names'参数")
        if not isinstance(self.config['source_names'], list):
            raise ValueError("'source_names'必须是一个列表")
        if len(self.config['source_names']) == 0:
            raise ValueError("'source_names'不能为空")
        
        if 'function' not in self.config:
            raise ValueError("非线性滞后模板需要'function'参数")
        
        function = self.config['function']
        if function not in ['sqrt', 'log', 'exp', 'power', 'custom']:
            raise ValueError(f"不支持的函数类型: {function}")
        
        if function == 'custom' and 'function_expr' not in self.config:
            raise ValueError("自定义函数需要'function_expr'参数")
    
    def get_dependencies(self) -> list:
        """获取依赖的数据名称"""
        return self.config['source_names']
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成非线性滞后关系数据
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 其他数据字典，必须包含所有source_names对应的数据
        
        Returns:
            生成的数据数组
        """
        if other_data is None:
            raise ValueError("非线性滞后模板需要other_data参数")
        
        source_names = self.config['source_names']
        function = self.config['function']
        lag_seconds = self.config.get('lag_seconds', 0)
        noise_level = self.config.get('noise_level', 0.0)
        
        # 检查所有源数据是否存在
        for source_name in source_names:
            if source_name not in other_data:
                raise ValueError(f"缺少依赖数据: {source_name}")
        
        # 计算滞后点数
        time_interval = time_points[1] - time_points[0] if len(time_points) > 1 else 5.0
        lag_points = int(round(lag_seconds / time_interval)) if lag_seconds > 0 else 0
        
        # 初始化输出数据
        data = np.zeros_like(time_points, dtype=float)
        
        # 生成非线性滞后关系数据
        for i in range(len(data)):
            # 计算滞后后的源数据索引
            source_idx = i - lag_points if lag_points > 0 else i
            
            if source_idx < 0:
                # 如果滞后索引小于0，使用源数据的第一个值
                source_idx = 0
            
            # 获取滞后后的源数据值
            source_values = [other_data[name][source_idx] for name in source_names]
            
            # 根据函数类型计算值
            if function == 'sqrt':
                # sqrt(x1 * x2 * ...) 或 sqrt(x1 + x2 + ...)
                operation = self.config.get('function_params', {}).get('operation', 'multiply')
                if operation == 'multiply':
                    value = np.prod(source_values)
                else:  # 'add'
                    value = np.sum(source_values)
                # 确保值非负
                data[i] = np.sqrt(max(0, value))
            
            elif function == 'log':
                # log(x1 + x2 + ...)
                value = np.sum(source_values)
                # 确保值大于0
                data[i] = np.log(max(1e-10, value))
            
            elif function == 'exp':
                # exp(x1 + x2 + ...)
                value = np.sum(source_values)
                data[i] = np.exp(value)
            
            elif function == 'power':
                # (x1 + x2 + ...)^n
                value = np.sum(source_values)
                power = self.config.get('function_params', {}).get('power', 2.0)
                data[i] = np.power(value, power)
            
            elif function == 'custom':
                # 自定义表达式
                function_expr = self.config['function_expr']
                # 这里需要实现表达式解析，暂时不支持
                raise NotImplementedError("自定义表达式功能尚未实现")
        
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, abs(data) * noise_level, size=len(data))
            data = data + noise
        
        return data

