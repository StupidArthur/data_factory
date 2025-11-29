"""
批量生成数据
"""

import yaml
from pathlib import Path
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.generators.data_generator import DataGenerator
from template.template_manager import TemplateManager
from output.data_exporter import DataExporter

def batch_generate(config_dir='config', output_dir='output'):
    """
    批量生成数据
    
    Args:
        config_dir: 配置文件目录
        output_dir: 输出目录
    """
    config_path = Path(config_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    yaml_files = list(config_path.glob('*.yaml')) + list(config_path.glob('*.yml'))
    
    for yaml_file in yaml_files:
        print(f"处理配置文件：{yaml_file.name}")
        
        try:
            # 加载配置
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 创建数据生成器
            generator_config = config.get('generator', {})
            generator = DataGenerator(generator_config)
            
            # 生成数据
            full_df = generator.generate()
            history_df = generator.get_history_data()
            
            # 创建模板管理器和导出器
            template_config = config.get('template', {})
            template_manager = TemplateManager(template_config)
            exporter = DataExporter(template_manager)
            
            # 生成时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = yaml_file.stem
            
            # 导出历史数据
            history_output = output_path / f"{base_name}_{timestamp}_history.csv"
            exporter.export(history_df, str(history_output), add_timestamp=False)
            print(f"  历史数据已导出：{history_output}")
            
            # 导出完整数据
            full_output = output_path / f"{base_name}_{timestamp}.csv"
            exporter.export(full_df, str(full_output), add_timestamp=False)
            print(f"  完整数据已导出：{full_output}")
            
        except Exception as e:
            print(f"  处理失败：{e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("批量生成完成")

if __name__ == '__main__':
    batch_generate('config', 'output')

