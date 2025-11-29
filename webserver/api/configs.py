"""
配置管理API

提供配置的增删改查功能。
"""

from sanic import Blueprint, json
from sanic.exceptions import NotFound, BadRequest
from sanic.response import text
from sqlalchemy.orm import Session
from webserver.models import get_db, Config, ConfigGroup
import yaml

configs_bp = Blueprint('configs', url_prefix='/api/configs')


# 注意：GET / 路由必须在 GET /<config_id:int> 之前定义，避免路由冲突
@configs_bp.get('/')
async def list_configs(request):
    """
    获取配置列表
    
    Query Parameters:
        group_id: 分组ID（可选，如果提供则只返回该分组的配置）
    
    Returns:
        配置列表（JSON格式）
    """
    db: Session = next(get_db())
    try:
        group_id = request.args.get('group_id')
        query = db.query(Config)
        
        # 如果指定了分组ID，过滤配置
        if group_id:
            try:
                group_id = int(group_id)
                query = query.filter(Config.group_id == group_id)
            except ValueError:
                pass
        
        configs = query.order_by(Config.id.asc()).all()
        return json({
            'success': True,
            'data': [config.to_dict() for config in configs]
        })
    except Exception as e:
        return json({
            'success': False,
            'error': f'加载配置列表失败: {str(e)}'
        }, status=500)
    finally:
        db.close()


@configs_bp.get('/<config_id:int>')
async def get_config(request, config_id: int):
    """
    获取单个配置
    
    Args:
        config_id: 配置ID
    
    Returns:
        配置详情（JSON格式）
    """
    db: Session = next(get_db())
    try:
        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            raise NotFound(f'配置 {config_id} 不存在')
        
        return json({
            'success': True,
            'data': config.to_dict()
        })
    finally:
        db.close()


@configs_bp.post('/')
async def create_config(request):
    """
    创建新配置
    
    Request Body:
        {
            "name": "配置名称",
            "config_yaml": "YAML配置内容"
        }
    
    Returns:
        创建的配置（JSON格式）
    """
    try:
        # 获取请求体数据
        data = request.json
        if not data:
            return json({
                'success': False,
                'error': '请求体不能为空'
            }, status=400)
        
        name = data.get('name')
        config_yaml = data.get('config_yaml')
        description = data.get('description', '')
        group_id = data.get('group_id')
        user = data.get('user')
        
        if not name:
            return json({
                'success': False,
                'error': '配置名称不能为空'
            }, status=400)
        if not config_yaml:
            return json({
                'success': False,
                'error': 'YAML配置不能为空'
            }, status=400)
        
        # 验证YAML格式
        try:
            yaml.safe_load(config_yaml)
        except yaml.YAMLError as e:
            return json({
                'success': False,
                'error': f'YAML格式错误: {str(e)}'
            }, status=400)
        
        db: Session = next(get_db())
        try:
            # 验证分组是否存在
            if group_id:
                group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
                if not group:
                    return json({
                        'success': False,
                        'error': f'分组 {group_id} 不存在'
                    }, status=400)
            
            config = Config(
                name=name,
                config_yaml=config_yaml,
                description=description,
                group_id=group_id,
                user=user
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            
            return json({
                'success': True,
                'data': config.to_dict()
            }, status=201)
        except Exception as e:
            db.rollback()
            return json({
                'success': False,
                'error': f'创建配置失败: {str(e)}'
            }, status=500)
        finally:
            db.close()
    except Exception as e:
        return json({
            'success': False,
            'error': f'创建配置失败: {str(e)}'
        }, status=500)


@configs_bp.put('/<config_id:int>')
async def update_config(request, config_id: int):
    """
    更新配置
    
    Args:
        config_id: 配置ID
    
    Request Body:
        {
            "name": "配置名称（可选）",
            "config_yaml": "YAML配置内容（可选）"
        }
    
    Returns:
        更新后的配置（JSON格式）
    """
    try:
        data = request.json
        if not data:
            return json({
                'success': False,
                'error': '请求体不能为空'
            }, status=400)
        
        db: Session = next(get_db())
        try:
            config = db.query(Config).filter(Config.id == config_id).first()
            if not config:
                return json({
                    'success': False,
                    'error': f'配置 {config_id} 不存在'
                }, status=404)
            
            # 更新名称
            if 'name' in data:
                config.name = data['name']
            
            # 更新描述
            if 'description' in data:
                config.description = data['description']
            
            # 更新分组
            if 'group_id' in data:
                group_id = data['group_id']
                if group_id:
                    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
                    if not group:
                        return json({
                            'success': False,
                            'error': f'分组 {group_id} 不存在'
                        }, status=400)
                config.group_id = group_id
            
            # 更新用户
            if 'user' in data:
                config.user = data['user']
            
            # 更新YAML配置
            if 'config_yaml' in data:
                config_yaml = data['config_yaml']
                # 验证YAML格式
                try:
                    yaml.safe_load(config_yaml)
                except yaml.YAMLError as e:
                    return json({
                        'success': False,
                        'error': f'YAML格式错误: {str(e)}'
                    }, status=400)
                config.config_yaml = config_yaml
            
            db.commit()
            db.refresh(config)
            
            return json({
                'success': True,
                'data': config.to_dict()
            })
        except Exception as e:
            db.rollback()
            return json({
                'success': False,
                'error': f'更新配置失败: {str(e)}'
            }, status=500)
        finally:
            db.close()
    except Exception as e:
        return json({
            'success': False,
            'error': f'更新配置失败: {str(e)}'
        }, status=500)


@configs_bp.delete('/<config_id:int>')
async def delete_config(request, config_id: int):
    """
    删除配置
    
    Args:
        config_id: 配置ID
    
    Returns:
        删除结果（JSON格式）
    """
    db: Session = next(get_db())
    try:
        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            raise NotFound(f'配置 {config_id} 不存在')
        
        db.delete(config)
        db.commit()
        
        return json({
            'success': True,
            'message': f'配置 {config_id} 已删除'
        })
    finally:
        db.close()


@configs_bp.post('/<config_id:int>/copy')
async def copy_config(request, config_id: int):
    """
    拷贝配置到新分组
    
    Args:
        config_id: 源配置ID
    
    Request Body:
        {
            "name": "新配置名称",
            "group_id": 目标分组ID（可选）,
            "description": "配置描述"（可选）
        }
    
    Returns:
        创建的配置（JSON格式）
    """
    db: Session = next(get_db())
    try:
        # 获取源配置
        source_config = db.query(Config).filter(Config.id == config_id).first()
        if not source_config:
            raise NotFound(f'配置 {config_id} 不存在')
        
        data = request.json
        if not data:
            return json({
                'success': False,
                'error': '请求体不能为空'
            }, status=400)
        
        name = data.get('name')
        if not name:
            return json({
                'success': False,
                'error': '配置名称不能为空'
            }, status=400)
        
        # 检查是否已存在同名配置，如果存在则自动重命名
        final_name = name
        counter = 1
        
        while True:
            existing_config = db.query(Config).filter(Config.name == final_name).first()
            if not existing_config:
                break
            # 如果存在同名配置，尝试添加后缀
            final_name = f"{name}_{counter}"
            counter += 1
        
        # 创建新配置（拷贝）
        new_config = Config(
            name=final_name,
            config_yaml=source_config.config_yaml,
            description=data.get('description', f'拷贝自：{source_config.name}'),
            group_id=data.get('group_id'),
            user=data.get('user'),
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        return json({
            'success': True,
            'data': new_config.to_dict(),
            'message': f'配置已拷贝，名称：{final_name}' if final_name != name else '配置拷贝成功'
        })
    finally:
        db.close()


@configs_bp.get('/check-name')
async def check_config_name(request):
    """
    检查配置名称并返回不重复的名称
    
    Query Parameters:
        name: 原始配置名称
    
    Returns:
        不重复的配置名称（JSON格式）
    """
    db: Session = next(get_db())
    try:
        name = request.args.get('name')
        if not name:
            return json({
                'success': False,
                'error': '配置名称不能为空'
            }, status=400)
        
        # 检查是否已存在同名配置，如果存在则自动重命名
        final_name = name
        counter = 1
        
        while True:
            existing_config = db.query(Config).filter(Config.name == final_name).first()
            if not existing_config:
                break
            # 如果存在同名配置，尝试添加后缀
            final_name = f"{name}_{counter}"
            counter += 1
        
        return json({
            'success': True,
            'name': final_name,
            'is_renamed': final_name != name
        })
    finally:
        db.close()


@configs_bp.get('/<config_id:int>/export')
async def export_config(request, config_id: int):
    """
    导出配置为YAML文件
    
    Args:
        config_id: 配置ID
    
    Returns:
        YAML文件内容
    """
    db: Session = next(get_db())
    try:
        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            raise NotFound(f'配置 {config_id} 不存在')
        
        # 返回YAML内容
        return text(
            config.config_yaml,
            headers={
                'Content-Type': 'text/yaml; charset=utf-8',
                'Content-Disposition': f'attachment; filename="{config.name}.yaml"'
            }
        )
    finally:
        db.close()


@configs_bp.post('/import')
async def import_config(request):
    """
    导入配置（从YAML文件）
    
    Request Body:
        {
            "name": "配置名称",
            "config_yaml": "YAML配置内容",
            "group_id": 分组ID（可选）,
            "description": "配置描述"（可选）
        }
    
    Returns:
        创建的配置（JSON格式）
    """
    try:
        data = request.json
        if not data:
            return json({
                'success': False,
                'error': '请求体不能为空'
            }, status=400)
        
        name = data.get('name')
        config_yaml = data.get('config_yaml')
        
        if not name or not config_yaml:
            return json({
                'success': False,
                'error': '配置名称和YAML内容不能为空'
            }, status=400)
        
        # 验证YAML格式
        try:
            yaml.safe_load(config_yaml)
        except yaml.YAMLError as e:
            return json({
                'success': False,
                'error': f'YAML格式错误: {str(e)}'
            }, status=400)
        
        db: Session = next(get_db())
        try:
            # 检查是否已存在同名配置，如果存在则自动重命名
            final_name = name
            counter = 1
            
            while True:
                existing_config = db.query(Config).filter(Config.name == final_name).first()
                if not existing_config:
                    break
                # 如果存在同名配置，尝试添加后缀
                final_name = f"{name}_{counter}"
                counter += 1
            
            # 创建配置
            config = Config(
                name=final_name,
                config_yaml=config_yaml,
                description=data.get('description', f'导入的配置：{final_name}'),
                group_id=data.get('group_id'),
                user=data.get('user'),
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            
            return json({
                'success': True,
                'data': config.to_dict(),
                'message': f'配置已导入，名称：{final_name}' if final_name != name else '配置导入成功'
            })
        finally:
            db.close()
    except Exception as e:
        return json({
            'success': False,
            'error': f'导入配置失败: {str(e)}'
        }, status=500)

