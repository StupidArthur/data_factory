"""
数据关系能力模板模块

提供各种数据生成能力模板，支持插件化扩展。
"""

from core.relationships.base import CapabilityTemplate, CompositeCapabilityTemplate
from core.relationships.time_pattern import TimePatternTemplate
from core.relationships.lag_follow import LagFollowTemplate
from core.relationships.polynomial import PolynomialTemplate
from core.relationships.random_pattern import RandomPatternTemplate
from core.relationships.nonlinear_lag import NonlinearLagTemplate

# 模板类型注册表
_TEMPLATE_REGISTRY = {
    'TimePatternTemplate': TimePatternTemplate,
    'LagFollowTemplate': LagFollowTemplate,
    'PolynomialTemplate': PolynomialTemplate,
    'RandomPatternTemplate': RandomPatternTemplate,
    'NonlinearLagTemplate': NonlinearLagTemplate,
    'CompositeCapabilityTemplate': CompositeCapabilityTemplate,
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
    'CompositeCapabilityTemplate',
    'TimePatternTemplate',
    'LagFollowTemplate',
    'PolynomialTemplate',
    'RandomPatternTemplate',
    'NonlinearLagTemplate',
    'get_template_class',
    'register_template',
]

