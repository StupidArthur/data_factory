"""
预设配置管理API

提供从config目录读取和导入预设配置的功能。
"""

from sanic import Blueprint, json
from sanic.exceptions import NotFound, BadRequest
from sqlalchemy.orm import Session
from webserver.models import get_db, Config, ConfigGroup
from pathlib import Path
import yaml
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

presets_bp = Blueprint('presets', url_prefix='/api/presets')


@presets_bp.get('/list')
async def list_preset_files(request):
    """
    列出config目录下的所有YAML文件
    
    Returns:
        预设配置文件列表（JSON格式）
    """
    try:
        config_dir = project_root / 'config'
        yaml_files = []
        
        if config_dir.exists():
            for file_path in config_dir.glob('*.yaml'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 尝试解析YAML以验证格式
                        yaml.load(content, Loader=yaml.FullLoader)
                        
                        yaml_files.append({
                            'filename': file_path.name,
                            'path': str(file_path.relative_to(project_root)),
                        })
                except Exception as e:
                    # 跳过无法解析的文件
                    continue
        
        return json({
            'success': True,
            'data': yaml_files,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json({
            'success': False,
            'error': f'读取预设文件列表失败: {str(e)}'
        }, status=500)


@presets_bp.post('/import')
async def import_presets(request):
    """
    导入所有预设配置到数据库
    
    Request Body:
        {
            "group_name": "预设配置"  // 可选，默认使用"预设配置"
        }
    
    Returns:
        导入结果（JSON格式）
    """
    db: Session = next(get_db())
    try:
        data = request.json or {}
        group_name = data.get('group_name', '预设配置')
        
        # 获取或创建预设分组
        preset_group = db.query(ConfigGroup).filter(ConfigGroup.name == group_name).first()
        if not preset_group:
            preset_group = ConfigGroup(name=group_name, description='系统预设的配置模板')
            db.add(preset_group)
            db.commit()
            db.refresh(preset_group)
        
        config_dir = project_root / 'config'
        imported_count = 0
        skipped_count = 0
        errors = []
        
        if config_dir.exists():
            for file_path in config_dir.glob('*.yaml'):
                try:
                    # 检查是否已存在同名配置
                    config_name = file_path.stem  # 文件名（不含扩展名）
                    existing_config = db.query(Config).filter(
                        Config.name == config_name,
                        Config.group_id == preset_group.id
                    ).first()
                    
                    if existing_config:
                        skipped_count += 1
                        continue
                    
                    # 读取YAML文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml_content = f.read()
                    
                    # 验证YAML格式
                    try:
                        yaml.load(yaml_content, Loader=yaml.FullLoader)
                    except Exception as e:
                        errors.append(f'{file_path.name}: YAML格式错误 - {str(e)}')
                        continue
                    
                    # 创建配置
                    config = Config(
                        name=config_name,
                        config_yaml=yaml_content,
                        description=f'预设配置：{config_name}',
                        group_id=preset_group.id,
                        user=None,
                    )
                    db.add(config)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f'{file_path.name}: {str(e)}')
                    continue
            
            db.commit()
        
        return json({
            'success': True,
            'message': f'导入完成：成功 {imported_count} 个，跳过 {skipped_count} 个',
            'data': {
                'imported': imported_count,
                'skipped': skipped_count,
                'errors': errors,
            },
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return json({
            'success': False,
            'error': f'导入预设配置失败: {str(e)}'
        }, status=500)
    finally:
        db.close()

