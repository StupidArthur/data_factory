"""
Sanic Web应用入口

提供数据工厂的Web界面和API服务。
"""

from sanic import Sanic
from sanic.response import file, json
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webserver.models import init_db
from webserver.api import configs, generate, export, groups, presets

# 创建Sanic应用
app = Sanic('DataFactory', strict_slashes=False)

# 添加CORS中间件
@app.middleware('request')
async def handle_options(request):
    """
    处理OPTIONS预检请求
    """
    if request.method == 'OPTIONS':
        from sanic.response import json as json_response
        # 返回响应，中断后续处理
        return json_response({}, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

@app.middleware('response')
async def add_cors_headers(request, response):
    """
    添加CORS响应头
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

# 注册API蓝图（Sanic不支持嵌套蓝图，需要直接注册各个蓝图）
# 注意：API路由需要在静态文件路由之前注册
app.blueprint(configs.configs_bp)
app.blueprint(generate.generate_bp)
app.blueprint(export.export_bp)
app.blueprint(groups.groups_bp)
app.blueprint(presets.presets_bp)

# 调试：打印所有注册的路由
if __name__ == '__main__':
    print("\n已注册的路由:")
    for route in app.router.routes_all.values():
        if 'api' in str(route.uri):
            print(f"  {list(route.methods)} {route.uri}")

# 静态文件目录（React 应用构建后的输出目录）
static_dir = Path(__file__).parent / 'static'


@app.get('/')
async def serve_index(request):
    """
    首页：返回 React 应用的 index.html
    """
    index_file = static_dir / 'index.html'
    if index_file.exists():
        return await file(str(index_file))
    return json({'error': '前端应用未构建，请先运行 npm run build'}, status=404)


@app.get('/<path:path>')
async def serve_static(request, path: str):
    """
    静态文件服务
    
    支持 React Router 的客户端路由：
    - 如果是静态资源文件（js/css/images等），返回对应文件
    - 否则返回 index.html，让 React Router 处理路由
    
    Args:
        path: 请求路径
    """
    # 排除 API 路径（应该已经被 API 路由处理了，这里作为双重保险）
    if path.startswith('api/'):
        return json({'error': 'API路径不存在'}, status=404)
    
    # 检查是否是静态资源文件
    file_path = static_dir / path
    if file_path.exists() and file_path.is_file():
        return await file(str(file_path))
    
    # 对于其他路径（React Router 路由），返回 index.html
    index_file = static_dir / 'index.html'
    if index_file.exists():
        return await file(str(index_file))
    
    return json({'error': '文件不存在'}, status=404)


@app.exception(Exception)
async def handle_exception(request, exception):
    """
    全局异常处理
    
    Args:
        request: 请求对象
        exception: 异常对象
    """
    import traceback
    traceback.print_exc()
    return json({
        'success': False,
        'error': str(exception)
    }, status=500)


def run_server(host='0.0.0.0', port=8000, debug=False):
    """
    运行Web服务器
    
    Args:
        host: 主机地址
        port: 端口号
        debug: 是否开启调试模式
    """
    # 初始化数据库
    init_db()
    
    # 运行服务器（Windows上使用单进程模式）
    app.run(host=host, port=port, debug=debug, single_process=True)


if __name__ == '__main__':
    # 配置参数
    host = '0.0.0.0'  # 监听地址
    port = 8000  # 端口号
    debug = True  # 是否开启调试模式
    
    # 运行服务器
    run_server(host=host, port=port, debug=debug)

