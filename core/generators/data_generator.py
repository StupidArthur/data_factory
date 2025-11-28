"""
数据生成器核心模块

负责协调多个能力模板，生成完整的时间序列数据集。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from core.relationships import get_template_class, CapabilityTemplate


class DataGenerator:
    """
    数据生成器
    
    根据配置加载能力模板，生成时间序列数据。
    """
    
    # 常量定义
    DEFAULT_TIME_INTERVAL = 5.0  # 默认时间间隔（秒）
    DEFAULT_HISTORY_POINTS = 10000  # 默认历史数据点数
    DEFAULT_FUTURE_POINTS = 120  # 默认未来数据点数（10分钟）
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据生成器
        
        Args:
            config: 配置字典，包含：
                - time_interval: 时间间隔（秒），默认5.0
                - history_points: 历史数据点数，默认10000
                - future_points: 未来数据点数，默认120
                - start_time: 起始时间（可选）
                - templates: 能力模板配置列表
        """
        self.config = config
        self.time_interval = config.get('time_interval', self.DEFAULT_TIME_INTERVAL)
        self.history_points = config.get('history_points', self.DEFAULT_HISTORY_POINTS)
        self.future_points = config.get('future_points', self.DEFAULT_FUTURE_POINTS)
        self.start_time = config.get('start_time', datetime(2024, 1, 1, 0, 0, 0))
        
        # 加载能力模板
        self.templates: Dict[str, CapabilityTemplate] = {}
        self._load_templates()
        
        # 生成时间点
        self.time_points = self._generate_time_points()
    
    def _load_templates(self):
        """加载能力模板"""
        templates_config = self.config.get('templates', [])
        
        for template_config in templates_config:
            template_type = template_config['type']
            template_name = template_config.get('name', template_type)
            template_class = get_template_class(template_type)
            template = template_class(template_config.get('config', {}))
            self.templates[template_name] = template
    
    def _generate_time_points(self) -> np.ndarray:
        """生成时间点数组"""
        total_points = self.history_points + self.future_points
        
        # 生成时间戳（秒为单位）
        if isinstance(self.start_time, str):
            start_dt = datetime.fromisoformat(self.start_time)
        else:
            start_dt = self.start_time
        
        start_timestamp = start_dt.timestamp()
        time_points = np.arange(
            start_timestamp,
            start_timestamp + total_points * self.time_interval,
            self.time_interval
        )[:total_points]
        
        return time_points
    
    def _resolve_dependencies(self) -> List[str]:
        """
        解析模板依赖关系，返回生成顺序
        
        Returns:
            模板名称的生成顺序列表
        """
        # 构建依赖图
        dependencies = {}
        for name, template in self.templates.items():
            dependencies[name] = template.get_dependencies()
        
        # 拓扑排序
        in_degree = {name: 0 for name in self.templates.keys()}
        for name, deps in dependencies.items():
            for dep in deps:
                # 检查依赖是否在模板中
                if dep in self.templates:
                    in_degree[name] += 1
        
        # 找到所有依赖的源数据（不在模板中的）
        external_deps = set()
        for deps in dependencies.values():
            for dep in deps:
                if dep not in self.templates:
                    external_deps.add(dep)
        
        # 生成顺序
        order = []
        queue = [name for name, degree in in_degree.items() if degree == 0]
        
        while queue:
            name = queue.pop(0)
            order.append(name)
            
            # 更新依赖该模板的其他模板的入度
            for other_name, deps in dependencies.items():
                if name in deps and other_name not in order:
                    in_degree[other_name] -= 1
                    if in_degree[other_name] == 0:
                        queue.append(other_name)
        
        # 检查是否有循环依赖
        if len(order) < len(self.templates):
            remaining = set(self.templates.keys()) - set(order)
            raise ValueError(f"检测到循环依赖或缺失依赖: {remaining}")
        
        return order
    
    def generate(self) -> pd.DataFrame:
        """
        生成完整的数据集
        
        Returns:
            DataFrame，包含timeStamp列和所有生成的数据列
        """
        # 解析依赖关系，确定生成顺序
        generation_order = self._resolve_dependencies()
        
        # 存储生成的数据
        generated_data: Dict[str, np.ndarray] = {}
        
        # 按顺序生成数据
        for template_name in generation_order:
            template = self.templates[template_name]
            
            # 准备依赖数据
            other_data = {}
            for dep_name in template.get_dependencies():
                if dep_name in generated_data:
                    other_data[dep_name] = generated_data[dep_name]
                else:
                    # 外部依赖，需要从配置中获取或使用默认值
                    raise ValueError(f"缺少外部依赖数据: {dep_name}")
            
            # 生成数据
            data = template.generate(self.time_points, other_data if other_data else None)
            output_name = template.get_output_name()
            generated_data[output_name] = data
        
        # 构建DataFrame
        df_data = {'timeStamp': self.time_points}
        df_data.update(generated_data)
        
        df = pd.DataFrame(df_data)
        
        return df
    
    def get_history_data(self) -> pd.DataFrame:
        """获取历史数据部分（前10000点）"""
        df = self.generate()
        return df.iloc[:self.history_points].copy()
    
    def get_future_data(self) -> pd.DataFrame:
        """获取未来数据部分（后120点）"""
        df = self.generate()
        return df.iloc[self.history_points:].copy()

