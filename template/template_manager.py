"""
模板管理模块

管理CSV输出模板的配置，支持不同的时间格式、标题行配置等。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd


class TemplateManager:
    """
    模板管理器
    
    管理数据输出的模板配置，包括：
    - 时间戳格式
    - 标题行配置
    - 列名和描述配置
    """
    
    # 时间格式常量
    TIME_FORMAT_TIMESTAMP = 'timestamp'  # Unix时间戳
    TIME_FORMAT_DATETIME = 'datetime'    # 2024-1-1 00:00:00
    TIME_FORMAT_DATETIME_SLASH = 'datetime_slash'  # 2024/1/1 00:00:05
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模板管理器
        
        Args:
            config: 配置字典，包含：
                - time_format: 时间格式（'timestamp', 'datetime', 'datetime_slash'）
                - has_title_row: 是否有标题行（第一行变量名）
                - has_description_row: 是否有描述行（第二行变量描述）
                - hide_parameter_descriptions: 是否隐藏参数描述（True使用"未知工况N"，False使用配置的描述）
                - column_descriptions: 列描述字典（可选）
        """
        self.config = config
        self.time_format = config.get('time_format', self.TIME_FORMAT_DATETIME)
        self.has_title_row = config.get('has_title_row', True)
        self.has_description_row = config.get('has_description_row', True)
        self.hide_parameter_descriptions = config.get('hide_parameter_descriptions', True)  # 默认隐藏
        self.column_descriptions = config.get('column_descriptions', {})
    
    def format_timestamp(self, timestamp: float) -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: Unix时间戳
        
        Returns:
            格式化后的时间字符串
        """
        dt = datetime.fromtimestamp(timestamp)
        
        if self.time_format == self.TIME_FORMAT_TIMESTAMP:
            return str(int(timestamp))
        elif self.time_format == self.TIME_FORMAT_DATETIME:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif self.time_format == self.TIME_FORMAT_DATETIME_SLASH:
            return dt.strftime('%Y/%m/%d %H:%M:%S')
        else:
            raise ValueError(f"不支持的时间格式: {self.time_format}")
    
    def get_column_names(self, df: pd.DataFrame) -> list:
        """
        获取列名列表（用于标题行）
        
        Args:
            df: DataFrame
        
        Returns:
            列名列表
        """
        return list(df.columns)
    
    def get_column_descriptions(self, df: pd.DataFrame) -> list:
        """
        获取列描述列表（用于描述行）
        
        根据hide_parameter_descriptions配置决定参数列的描述：
        - True: 使用"未知工况1"、"未知工况2"等
        - False: 使用配置文件中column_descriptions指定的描述
        
        Args:
            df: DataFrame
        
        Returns:
            列描述列表
        """
        descriptions = []
        condition_index = 1  # 工况编号从1开始
        
        for col in df.columns:
            if col == 'timeStamp':
                # 时间戳列保持原描述或使用默认
                if col in self.column_descriptions:
                    descriptions.append(self.column_descriptions[col])
                else:
                    descriptions.append('时间戳')
            else:
                # 参数列描述
                if self.hide_parameter_descriptions:
                    # 隐藏参数描述，使用"未知工况N"格式
                    descriptions.append(f'未知工况{condition_index}')
                    condition_index += 1
                else:
                    # 显示参数描述，使用配置中的描述
                    if col in self.column_descriptions:
                        descriptions.append(self.column_descriptions[col])
                    else:
                        # 如果配置中没有描述，使用"未知工况N"作为后备
                        descriptions.append(f'未知工况{condition_index}')
                        condition_index += 1
        
        return descriptions
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        格式化DataFrame（转换时间戳格式）
        
        Args:
            df: 原始DataFrame
        
        Returns:
            格式化后的DataFrame
        """
        df_formatted = df.copy()
        
        # 格式化时间戳列
        if 'timeStamp' in df_formatted.columns:
            df_formatted['timeStamp'] = df_formatted['timeStamp'].apply(self.format_timestamp)
        
        return df_formatted

