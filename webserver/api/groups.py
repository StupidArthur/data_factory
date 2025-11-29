"""
分组管理API

提供配置分组的增删改查功能。
"""

from sanic import Blueprint, json
from sanic.exceptions import NotFound, BadRequest
from sqlalchemy.orm import Session
from webserver.models import get_db, ConfigGroup, Config
import yaml

groups_bp = Blueprint('groups', url_prefix='/api/groups')


@groups_bp.get('/')
async def list_groups(request):
    """
    获取分组列表
    
    Returns:
        分组列表（JSON格式）
    """
    db: Session = next(get_db())
    try:
        groups = db.query(ConfigGroup).order_by(ConfigGroup.created_at.desc()).all()
        return json({
            'success': True,
            'data': [group.to_dict() for group in groups]
        })
    except Exception as e:
        return json({
            'success': False,
            'error': f'加载分组列表失败: {str(e)}'
        }, status=500)
    finally:
        db.close()


@groups_bp.get('/<group_id:int>')
async def get_group(request, group_id: int):
    """
    获取单个分组
    
    Args:
        group_id: 分组ID
    
    Returns:
        分组详情（JSON格式）
    """
    db: Session = next(get_db())
    try:
        group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
        if not group:
            return json({
                'success': False,
                'error': f'分组 {group_id} 不存在'
            }, status=404)
        
        return json({
            'success': True,
            'data': group.to_dict()
        })
    finally:
        db.close()


@groups_bp.post('/')
async def create_group(request):
    """
    创建新分组
    
    Request Body:
        {
            "name": "分组名称",
            "description": "分组描述（可选）"
        }
    
    Returns:
        创建的分组（JSON格式）
    """
    try:
        data = request.json
        if not data:
            return json({
                'success': False,
                'error': '请求体不能为空'
            }, status=400)
        
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return json({
                'success': False,
                'error': '分组名称不能为空'
            }, status=400)
        
        db: Session = next(get_db())
        try:
            # 检查分组名是否已存在
            existing_group = db.query(ConfigGroup).filter(ConfigGroup.name == name).first()
            if existing_group:
                return json({
                    'success': False,
                    'error': f'分组名称"{name}"已存在'
                }, status=400)
            
            group = ConfigGroup(name=name, description=description)
            db.add(group)
            db.commit()
            db.refresh(group)
            
            return json({
                'success': True,
                'data': group.to_dict()
            }, status=201)
        except Exception as e:
            db.rollback()
            return json({
                'success': False,
                'error': f'创建分组失败: {str(e)}'
            }, status=500)
        finally:
            db.close()
    except Exception as e:
        return json({
            'success': False,
            'error': f'创建分组失败: {str(e)}'
        }, status=500)


@groups_bp.put('/<group_id:int>')
async def update_group(request, group_id: int):
    """
    更新分组
    
    Args:
        group_id: 分组ID
    
    Request Body:
        {
            "name": "分组名称（可选）",
            "description": "分组描述（可选）"
        }
    
    Returns:
        更新后的分组（JSON格式）
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
            group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
            if not group:
                return json({
                    'success': False,
                    'error': f'分组 {group_id} 不存在'
                }, status=404)
            
            # 不能修改"已删除"分组
            if group.name == '已删除':
                return json({
                    'success': False,
                    'error': '不能修改"已删除"分组'
                }, status=400)
            
            # 更新名称
            if 'name' in data:
                new_name = data['name']
                if new_name != group.name:
                    # 检查新名称是否已存在
                    existing_group = db.query(ConfigGroup).filter(ConfigGroup.name == new_name).first()
                    if existing_group:
                        return json({
                            'success': False,
                            'error': f'分组名称"{new_name}"已存在'
                        }, status=400)
                    group.name = new_name
            
            # 更新描述
            if 'description' in data:
                group.description = data['description']
            
            db.commit()
            db.refresh(group)
            
            return json({
                'success': True,
                'data': group.to_dict()
            })
        except Exception as e:
            db.rollback()
            return json({
                'success': False,
                'error': f'更新分组失败: {str(e)}'
            }, status=500)
        finally:
            db.close()
    except Exception as e:
        return json({
            'success': False,
            'error': f'更新分组失败: {str(e)}'
        }, status=500)


@groups_bp.delete('/<group_id:int>')
async def delete_group(request, group_id: int):
    """
    删除分组
    
    删除分组后，该分组下的所有配置将移动到"已删除"分组。
    
    Args:
        group_id: 分组ID
    
    Returns:
        删除结果（JSON格式）
    """
    db: Session = next(get_db())
    try:
        group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
        if not group:
            return json({
                'success': False,
                'error': f'分组 {group_id} 不存在'
            }, status=404)
        
        # 不能删除"已删除"分组
        if group.name == '已删除':
            return json({
                'success': False,
                'error': '不能删除"已删除"分组'
            }, status=400)
        
        # 获取"已删除"分组
        deleted_group = db.query(ConfigGroup).filter(ConfigGroup.name == '已删除').first()
        if not deleted_group:
            # 如果不存在，创建它
            deleted_group = ConfigGroup(name='已删除', description='已删除的配置分组')
            db.add(deleted_group)
            db.flush()
        
        # 将该分组下的所有配置移动到"已删除"分组
        configs = db.query(Config).filter(Config.group_id == group_id).all()
        for config in configs:
            config.group_id = deleted_group.id
        
        # 删除分组
        db.delete(group)
        db.commit()
        
        return json({
            'success': True,
            'message': f'分组 {group_id} 已删除，其下的 {len(configs)} 个配置已移动到"已删除"分组'
        })
    except Exception as e:
        db.rollback()
        return json({
            'success': False,
            'error': f'删除分组失败: {str(e)}'
        }, status=500)
    finally:
        db.close()

