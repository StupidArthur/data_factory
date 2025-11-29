"""
数据关系能力模板模块

提供各种数据生成能力模板，支持插件化扩展。

注意：当前版本只支持ExpressionTemplate，旧的模板类型（TimePatternTemplate、LagFollowTemplate等）已被移除。
"""

from core.relationships.base import CapabilityTemplate
from core.relationships.expression import ExpressionTemplate

# 模板类型注册表（只支持ExpressionTemplate）
_TEMPLATE_REGISTRY = {
    'ExpressionTemplate': ExpressionTemplate,
}


def get_template_class(template_type: str):
    """
    根据模板类型名称获取模板类
    
    Args:
        template_type: 模板类型名称
    
    Returns:
        模板类
    
    Raises:
        ValueError: 模板类型不存在时抛出异常
    """
    if template_type not in _TEMPLATE_REGISTRY:
        raise ValueError(f"未知的模板类型: {template_type}")
    return _TEMPLATE_REGISTRY[template_type]


def register_template(template_type: str, template_class):
    """
    注册新的模板类型
    
    Args:
        template_type: 模板类型名称
        template_class: 模板类（必须继承自CapabilityTemplate）
    """
    if not issubclass(template_class, CapabilityTemplate):
        raise ValueError(f"模板类必须继承自CapabilityTemplate")
    _TEMPLATE_REGISTRY[template_type] = template_class


__all__ = [
    'CapabilityTemplate',
    'ExpressionTemplate',
    'get_template_class',
    'register_template',
]

