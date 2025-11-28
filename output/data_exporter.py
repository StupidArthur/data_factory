"""
数据输出模块

负责将生成的数据按照模板配置输出到文件。
与模板管理模块分离，只负责数据输出逻辑。
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
from template.template_manager import TemplateManager
from utils.logger import get_logger


class DataExporter:
    """
    数据导出器
    
    负责将数据按照模板配置导出到CSV文件。
    """
    
    def __init__(self, template_manager: TemplateManager):
        """
        初始化数据导出器
        
        Args:
            template_manager: 模板管理器实例
        """
        self.template_manager = template_manager
        self.logger = get_logger()
    
    def export(self, 
               df: pd.DataFrame, 
               output_path: str,
               add_timestamp: bool = True) -> str:
        """
        导出数据到CSV文件
        
        Args:
            df: 要导出的DataFrame
            output_path: 输出文件路径
            add_timestamp: 是否在文件名中添加时间戳
        
        Returns:
            实际输出的文件路径
        """
        # 处理输出路径
        output_file = Path(output_path)
        
        # 如果需要添加时间戳
        if add_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stem = output_file.stem
            suffix = output_file.suffix
            output_file = output_file.parent / f"{stem}_{timestamp}{suffix}"
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 格式化数据
        df_formatted = self.template_manager.format_dataframe(df)
        
        # 准备输出内容
        lines = []
        
        # 添加标题行
        if self.template_manager.has_title_row:
            column_names = self.template_manager.get_column_names(df_formatted)
            lines.append(','.join(column_names))
        
        # 添加描述行
        if self.template_manager.has_description_row:
            column_descriptions = self.template_manager.get_column_descriptions(df_formatted)
            lines.append(','.join(column_descriptions))
        
        # 添加数据行
        for _, row in df_formatted.iterrows():
            line = ','.join([str(val) for val in row.values])
            lines.append(line)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(lines))
        
        self.logger.info(f"数据已导出到: {output_file}")
        
        return str(output_file)
    
    def export_incremental(self,
                          df: pd.DataFrame,
                          output_path: str,
                          chunk_size: int = 1000) -> str:
        """
        增量式导出数据（适用于大数据集）
        
        Args:
            df: 要导出的DataFrame
            output_path: 输出文件路径
            chunk_size: 每次写入的数据块大小
        
        Returns:
            实际输出的文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 格式化数据
        df_formatted = self.template_manager.format_dataframe(df)
        
        # 打开文件准备写入
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # 写入标题行
            if self.template_manager.has_title_row:
                column_names = self.template_manager.get_column_names(df_formatted)
                f.write(','.join(column_names) + '\n')
            
            # 写入描述行
            if self.template_manager.has_description_row:
                column_descriptions = self.template_manager.get_column_descriptions(df_formatted)
                f.write(','.join(column_descriptions) + '\n')
            
            # 增量写入数据
            total_rows = len(df_formatted)
            for i in range(0, total_rows, chunk_size):
                chunk = df_formatted.iloc[i:i+chunk_size]
                for _, row in chunk.iterrows():
                    line = ','.join([str(val) for val in row.values])
                    f.write(line + '\n')
                
                # 记录进度
                if (i + chunk_size) % (chunk_size * 10) == 0:
                    self.logger.info(f"已导出 {min(i + chunk_size, total_rows)}/{total_rows} 行数据")
        
        self.logger.info(f"数据已增量导出到: {output_file}")
        
        return str(output_file)

