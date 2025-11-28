"""
数据工厂主程序入口

提供数据生成、导出、可视化等功能。
"""

import yaml
from pathlib import Path
from datetime import datetime
from core.generators.data_generator import DataGenerator
from template.template_manager import TemplateManager
from output.data_exporter import DataExporter
from visualization.data_viewer import show_data_viewer
from utils.logger import get_logger
import sys


def load_config(config_path: str) -> dict:
    """
    加载配置文件（支持YAML格式）
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        # 根据文件扩展名判断格式
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            config = yaml.safe_load(f)
        else:
            # 兼容JSON格式
            import json
            config = json.load(f)
    return config


def generate_data(config_path: str, output_path: str = None, preview: bool = False):
    """
    生成数据
    
    Args:
        config_path: 配置文件路径
        output_path: 输出文件路径（可选）
        preview: 是否预览数据
    """
    logger = get_logger()
    
    # 加载配置
    logger.info(f"加载配置文件: {config_path}")
    config = load_config(config_path)
    
    # 创建数据生成器
    generator_config = config.get('generator', {})
    generator = DataGenerator(generator_config)
    logger.info("数据生成器已创建")
    
    # 生成数据
    logger.info("开始生成数据...")
    df = generator.generate()
    logger.info(f"数据生成完成，共 {len(df)} 行，{len(df.columns)} 列")
    
    # 预览数据
    if preview:
        logger.info("打开数据预览窗口...")
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        viewer = show_data_viewer(df)
        sys.exit(app.exec())
    
    # 导出数据
    if output_path:
        # 创建模板管理器
        template_config = config.get('template', {})
        template_manager = TemplateManager(template_config)
        
        # 创建数据导出器
        exporter = DataExporter(template_manager)
        
        # 获取历史数据和完整数据
        history_df = generator.get_history_data()
        full_df = df  # 完整数据（包含未来120点）
        
        # 生成时间戳（两个文件使用相同的时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成历史数据文件名（时间戳在history前面）
        output_file = Path(output_path)
        history_output_path = output_file.parent / f"{output_file.stem}_{timestamp}_history{output_file.suffix}"
        
        # 导出历史数据（10000点）
        history_actual_path = exporter.export(history_df, str(history_output_path), add_timestamp=False)
        logger.info(f"历史数据已导出到: {history_actual_path} (共 {len(history_df)} 行)")
        
        # 导出完整数据（10120点，包含未来120点）
        # 修改输出路径，确保时间戳一致
        full_output_path = output_file.parent / f"{output_file.stem}_{timestamp}{output_file.suffix}"
        full_actual_path = exporter.export(full_df, str(full_output_path), add_timestamp=False)
        logger.info(f"完整数据已导出到: {full_actual_path} (共 {len(full_df)} 行，包含未来 {generator.future_points} 点)")
    else:
        logger.info("未指定输出路径，数据未导出")


if __name__ == '__main__':
    # 配置参数
    config_path = 'config/test_case_04d_polynomial_sine_lag.yaml'  # 配置文件路径（支持YAML和JSON）
    output_path = 'output/test_case_04d_polynomial_sine_lag.csv'  # 输出文件路径（None表示不导出）
    preview = False  # 是否预览数据（True表示预览，False表示导出）
    
    # 生成数据
    generate_data(config_path, output_path, preview)

