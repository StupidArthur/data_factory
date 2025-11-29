"""
数据导出API

提供CSV文件导出功能。
"""

from sanic import Blueprint
from sanic.response import file_stream
from sanic.exceptions import NotFound, BadRequest
from sqlalchemy.orm import Session
from webserver.models import get_db, Config
import yaml
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.generators.data_generator import DataGenerator
from template.template_manager import TemplateManager
from output.data_exporter import DataExporter

export_bp = Blueprint('export', url_prefix='/api/export')


@export_bp.get('/<config_id:int>')
async def export_csv(request, config_id: int):
    """
    导出CSV文件
    
    Args:
        config_id: 配置ID
    
    Query Parameters:
        type: 导出类型（'history'或'full'，默认'full'）
    
    Returns:
        CSV文件流
    """
    try:
        export_type = request.args.get('type', 'full')  # 'history' 或 'full'
        
        db: Session = next(get_db())
        try:
            config = db.query(Config).filter(Config.id == config_id).first()
            if not config:
                raise NotFound(f'配置 {config_id} 不存在')
            config_yaml = config.config_yaml
            config_name = config.name
        finally:
            db.close()
        
        # 解析YAML配置
        try:
            config_dict = yaml.safe_load(config_yaml)
        except yaml.YAMLError as e:
            raise BadRequest(f'YAML格式错误: {str(e)}')
        
        # 创建数据生成器
        generator_config = config_dict.get('generator', {})
        generator = DataGenerator(generator_config)
        
        # 获取数据
        if export_type == 'history':
            df = generator.get_history_data()
            suffix = '_history'
        else:
            df = generator.generate()
            suffix = ''
        
        # 创建模板管理器
        template_config = config_dict.get('template', {})
        template_manager = TemplateManager(template_config)
        
        # 创建数据导出器
        exporter = DataExporter(template_manager)
        
        # 创建临时文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_{timestamp}{suffix}.csv"
        
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / 'data_factory_export'
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / filename
        
        # 导出数据
        exporter.export(df, str(temp_file), add_timestamp=False)
        
        # 返回文件流
        return await file_stream(
            str(temp_file),
            mime_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except (BadRequest, NotFound) as e:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise BadRequest(f'导出数据失败: {str(e)}')

