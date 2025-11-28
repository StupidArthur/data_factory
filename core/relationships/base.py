"""
能力模板基类和接口定义

能力模板系统采用插件化架构，每个能力模板都是一个独立的数据生成能力单元。
通过组合不同的能力模板，可以生成复杂的数据关系。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class CapabilityTemplate(ABC):
    """
    能力模板基类
    
    所有数据生成能力模板都需要继承此类，并实现generate方法。
    能力模板是数据生成的最小单元，可以独立使用，也可以组合使用。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化能力模板
        
        Args:
            config: 配置字典，包含该能力模板的所有参数
        """
        self.config = config
        self.name = config.get('name', self.__class__.__name__)
        self.validate_config()
    
    @abstractmethod
    def validate_config(self):
        """
        验证配置参数的有效性
        
        Raises:
            ValueError: 配置参数无效时抛出异常
        """
        pass
    
    @abstractmethod
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成数据
        
        Args:
            time_points: 时间点数组（秒为单位的时间戳）
            other_data: 其他数据字典，用于依赖关系（如滞后跟随、多项式关系等）
                       键为数据名称，值为对应的数据数组
        
        Returns:
            生成的数据数组，长度与time_points相同
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        获取该能力模板依赖的其他数据名称列表
        
        Returns:
            依赖的数据名称列表，如果无依赖则返回空列表
        """
        return []
    
    def get_output_name(self) -> str:
        """
        获取该能力模板输出的数据名称
        
        Returns:
            输出的数据名称
        """
        return self.config.get('output_name', self.name)


class CompositeCapabilityTemplate(CapabilityTemplate):
    """
    组合能力模板
    
    可以将多个能力模板组合在一起，支持：
    - 线性组合：result = w1*template1 + w2*template2 + ...
    - 乘积组合：result = template1 * template2 * ...
    - 自定义组合函数
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化组合能力模板
        
        Config格式：
        {
            'name': 'composite_template',
            'templates': [
                {'type': 'TimePatternTemplate', 'config': {...}, 'weight': 1.0},
                {'type': 'LagFollowTemplate', 'config': {...}, 'weight': 0.5}
            ],
            'combination_mode': 'linear'  # 'linear', 'multiply', 'custom'
        }
        """
        super().__init__(config)
        self.templates = []
        self.combination_mode = config.get('combination_mode', 'linear')
        self._load_templates()
    
    def _load_templates(self):
        """加载子模板"""
        from core.relationships import get_template_class
        
        for template_config in self.config.get('templates', []):
            template_type = template_config['type']
            template_class = get_template_class(template_type)
            template = template_class(template_config['config'])
            template.weight = template_config.get('weight', 1.0)
            self.templates.append(template)
    
    def validate_config(self):
        """验证配置"""
        if 'templates' not in self.config:
            raise ValueError("组合模板必须包含'templates'配置")
        if not isinstance(self.config['templates'], list):
            raise ValueError("'templates'必须是一个列表")
        if len(self.config['templates']) == 0:
            raise ValueError("'templates'不能为空")
    
    def get_dependencies(self) -> List[str]:
        """获取所有子模板的依赖"""
        dependencies = []
        for template in self.templates:
            dependencies.extend(template.get_dependencies())
        return list(set(dependencies))
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """生成组合数据"""
        results = []
        for template in self.templates:
            result = template.generate(time_points, other_data)
            results.append((result, template.weight))
        
        if self.combination_mode == 'linear':
            # 线性组合
            combined = np.zeros_like(time_points, dtype=float)
            for result, weight in results:
                combined += result * weight
            return combined
        elif self.combination_mode == 'multiply':
            # 乘积组合
            combined = np.ones_like(time_points, dtype=float)
            for result, weight in results:
                combined *= (result ** weight)
            return combined
        else:
            raise ValueError(f"不支持的组合模式: {self.combination_mode}")

