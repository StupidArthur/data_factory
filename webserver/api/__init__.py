"""
API路由模块

定义所有API路由的蓝图。
"""

from sanic import Blueprint

# 创建API蓝图（作为容器，统一URL前缀）
api_bp = Blueprint('api', url_prefix='/api')

# 导入各个API模块（延迟导入避免循环依赖）
from webserver.api import configs, generate, export, groups

# 注意：Sanic不支持嵌套蓝图，需要在app.py中直接注册各个蓝图
# 这里只导出蓝图对象，供app.py使用

