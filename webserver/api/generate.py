"""
数据生成API

提供数据生成和预览功能。
"""

from sanic import Blueprint, json
from sanic.exceptions import NotFound, BadRequest
from sqlalchemy.orm import Session
from webserver.models import get_db, Config
import yaml
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.generators.data_generator import DataGenerator

generate_bp = Blueprint('generate', url_prefix='/api/generate')


@generate_bp.post('/')
async def generate_data(request):
    """
    生成数据
    
    Request Body:
        {
            "config_id": 配置ID（可选，如果提供则使用数据库中的配置）
            或
            "config_yaml": "YAML配置内容"（可选，如果提供则直接使用）
        }
    
    Returns:
        生成的数据（JSON格式，包含历史数据和完整数据）
    """
    try:
        data = request.json or {}
        config_yaml = None
        
        # 如果提供了config_id，从数据库加载配置
        if 'config_id' in data:
            config_id = data['config_id']
            db: Session = next(get_db())
            try:
                config = db.query(Config).filter(Config.id == config_id).first()
                if not config:
                    raise NotFound(f'配置 {config_id} 不存在')
                config_yaml = config.config_yaml
            finally:
                db.close()
        # 如果提供了config_yaml，直接使用
        elif 'config_yaml' in data:
            config_yaml = data['config_yaml']
        else:
            raise BadRequest('必须提供config_id或config_yaml')
        
        # 解析YAML配置
        try:
            config_dict = yaml.safe_load(config_yaml)
        except yaml.YAMLError as e:
            raise BadRequest(f'YAML格式错误: {str(e)}')
        
        # 创建数据生成器
        generator_config = config_dict.get('generator', {})
        generator = DataGenerator(generator_config)
        
        # 生成数据
        full_df = generator.generate()
        history_df = generator.get_history_data()
        
        # 转换为JSON格式（只返回前1000行用于预览，避免数据过大）
        preview_rows = 1000
        full_preview = full_df.head(preview_rows).to_dict('records')
        history_preview = history_df.head(preview_rows).to_dict('records')
        
        # 获取列名
        columns = list(full_df.columns)
        
        return json({
            'success': True,
            'data': {
                'full_data': full_preview,
                'history_data': history_preview,
                'columns': columns,
                'total_rows': len(full_df),
                'history_rows': len(history_df),
                'future_rows': len(full_df) - len(history_df)
            }
        })
    except (BadRequest, NotFound) as e:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise BadRequest(f'生成数据失败: {str(e)}')


@generate_bp.get('/preview/<config_id:int>')
async def preview_data(request, config_id: int):
    """
    预览数据（用于图表展示）
    
    Args:
        config_id: 配置ID
    
    Returns:
        预览数据（JSON格式，返回所有数据点，但只包含数值列）
    """
    try:
        db: Session = next(get_db())
        try:
            config = db.query(Config).filter(Config.id == config_id).first()
            if not config:
                raise NotFound(f'配置 {config_id} 不存在')
            config_yaml = config.config_yaml
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
        
        # 生成数据
        df = generator.generate()
        
        # 转换为图表数据格式
        # 时间戳列
        timestamps = df['timeStamp'].tolist()
        
        # 数值列数据
        numeric_columns = [col for col in df.columns if col != 'timeStamp']
        series_data = {}
        for col in numeric_columns:
            series_data[col] = df[col].tolist()
        
        return json({
            'success': True,
            'data': {
                'timestamps': timestamps,
                'series': series_data,
                'columns': list(df.columns)
            }
        })
    except (BadRequest, NotFound) as e:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise BadRequest(f'预览数据失败: {str(e)}')

