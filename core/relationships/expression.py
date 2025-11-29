"""
表达式模板

完全统一的表达式模板，支持独立生成和依赖生成两种模式。
- 独立生成：表达式使用 t（时间）作为变量
- 依赖生成：表达式使用 x1, x2, x3（其他位号）作为变量
"""

import numpy as np
import ast
from typing import Dict, Any, Optional, List
from core.relationships.base import CapabilityTemplate


class SafeExpressionEvaluator:
    """
    安全的表达式求值器
    
    使用AST解析，只允许数学运算和预定义函数，不允许Python代码执行。
    """
    
    # 允许的函数（不包括random和random_normal，它们需要特殊处理）
    ALLOWED_FUNCTIONS = {
        'sqrt': np.sqrt,
        'log': np.log,
        'exp': np.exp,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'abs': np.abs,
        'max': np.maximum,
        'min': np.minimum,
        'power': np.power,
        'sign': np.sign,
        'random': None,  # 特殊处理
        'random_normal': None,  # 特殊处理
    }
    
    # 允许的运算符
    ALLOWED_OPS = {
        ast.Add: np.add,
        ast.Sub: np.subtract,
        ast.Mult: np.multiply,
        ast.Div: np.true_divide,
        ast.Pow: np.power,
        ast.Mod: np.mod,
        ast.USub: np.negative,
        ast.UAdd: lambda x: x,  # 正号，不做任何操作
    }
    
    def evaluate(self, expression: str, variables: Dict[str, Any]) -> np.ndarray:
        """
        安全地执行表达式
        
        Args:
            expression: Python数学表达式字符串
            variables: 变量字典，如 {'x1': array1, 'x2': array2, 't': time_array, ...}
        
        Returns:
            计算结果数组
        
        Raises:
            ValueError: 表达式错误或包含不允许的操作
        """
        try:
            # 解析AST
            tree = ast.parse(expression, mode='eval')
            # 验证AST（只允许数学运算）
            self._validate_ast(tree)
            # 执行AST
            result = self._eval_ast(tree.body, variables)
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"表达式计算错误: {str(e)}")
    
    def _validate_ast(self, node):
        """
        验证AST节点，确保只包含安全的操作
        
        Raises:
            ValueError: 如果包含不允许的操作
        """
        if isinstance(node, ast.Expression):
            self._validate_ast(node.body)
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.ALLOWED_OPS:
                raise ValueError(f"不允许的运算符: {type(node.op).__name__}")
            self._validate_ast(node.left)
            self._validate_ast(node.right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.ALLOWED_OPS:
                raise ValueError(f"不允许的运算符: {type(node.op).__name__}")
            self._validate_ast(node.operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("函数调用必须是函数名")
            if node.func.id not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"不允许的函数: {node.func.id}")
            for arg in node.args:
                self._validate_ast(arg)
            # 检查关键字参数（暂时不支持）
            if node.keywords:
                raise ValueError("函数调用不支持关键字参数")
        elif isinstance(node, ast.Name):
            # 变量名，允许
            pass
        elif isinstance(node, ast.Constant):
            # 常量，允许
            pass
        elif isinstance(node, ast.Num):  # Python < 3.8
            # 数字常量，允许
            pass
        else:
            raise ValueError(f"不允许的AST节点: {type(node).__name__}")
    
    def _eval_ast(self, node, variables: Dict[str, Any]) -> np.ndarray:
        """
        执行AST节点
        
        Args:
            node: AST节点
            variables: 变量字典
        
        Returns:
            计算结果数组
        """
        if isinstance(node, ast.Constant):
            value = node.value
            # 如果是标量，转换为数组
            if isinstance(value, (int, float)):
                # 获取数组长度（从variables中任意一个数组获取）
                array_length = len(next(iter(variables.values()))) if variables else 1
                return np.full(array_length, value, dtype=float)
            return value
        elif isinstance(node, ast.Num):  # Python < 3.8
            value = node.n
            array_length = len(next(iter(variables.values()))) if variables else 1
            return np.full(array_length, value, dtype=float)
        elif isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(f"未定义的变量: {node.id}")
            value = variables[node.id]
            # 如果是函数，返回函数本身（用于函数调用）
            if callable(value):
                return value
            # 如果是标量，转换为数组
            if isinstance(value, (int, float)):
                array_length = len(next(iter([v for v in variables.values() if isinstance(v, np.ndarray)]))) if variables else 1
                return np.full(array_length, value, dtype=float)
            return value
        elif isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left, variables)
            right = self._eval_ast(node.right, variables)
            op = self.ALLOWED_OPS[type(node.op)]
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_ast(node.operand, variables)
            op = self.ALLOWED_OPS[type(node.op)]
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"不允许的函数: {func_name}")
            
            args = [self._eval_ast(arg, variables) for arg in node.args]
            
            # 特殊处理random函数
            if func_name == 'random':
                # 获取数组长度（从variables中任意一个数组获取）
                array_length = None
                for v in variables.values():
                    if isinstance(v, np.ndarray):
                        array_length = len(v)
                        break
                if array_length is None:
                    raise ValueError("无法确定数组长度，random函数需要至少一个数组变量")
                return np.random.random(array_length)
            elif func_name == 'random_normal':
                # 获取数组长度
                array_length = None
                for v in variables.values():
                    if isinstance(v, np.ndarray):
                        array_length = len(v)
                        break
                if array_length is None:
                    raise ValueError("无法确定数组长度，random_normal函数需要至少一个数组变量")
                mean = float(args[0]) if len(args) > 0 else 0.0
                std = float(args[1]) if len(args) > 1 else 1.0
                return np.random.normal(mean, std, array_length)
            
            # 普通函数
            func = self.ALLOWED_FUNCTIONS[func_name]
            if func is None:
                raise ValueError(f"函数 {func_name} 需要特殊处理，但处理逻辑未实现")
            return func(*args)
        else:
            raise ValueError(f"不支持的AST节点: {type(node).__name__}")


class ExpressionTemplate(CapabilityTemplate):
    """
    表达式模板（完全统一）
    
    支持两种模式：
    1. 独立生成：表达式使用 t（时间）作为变量
    2. 依赖生成：表达式使用 x1, x2, x3（其他位号）作为变量
    
    Config格式（独立生成）：
    {
        'name': 'light_intensity',
        'output_name': 'F.light',
        'type': 'ExpressionTemplate',
        'calculation': {
            'expression': '50 + 100 * sin(2 * pi * t / 86400)',
        },
        'noise_level': 0.05,
    }
    
    Config格式（依赖生成）：
    {
        'name': 'composite_output',
        'output_name': 'F.composite',
        'type': 'ExpressionTemplate',
        'sources': [
            {'source_name': 'F.power', 'lag_seconds': 30},
            {'source_name': 'F.temperature', 'lag_seconds': 60},
        ],
        'calculation': {
            'expression': 'x1 * 0.5 + sin(x2) + sqrt(x3) + 10',
        },
        'noise_level': 0.05,
    }
    """
    
    def validate_config(self):
        """验证配置"""
        if 'calculation' not in self.config:
            raise ValueError("表达式模板需要'calculation'配置")
        if 'expression' not in self.config['calculation']:
            raise ValueError("calculation需要'expression'字段")
        
        expression = self.config['calculation']['expression']
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("expression必须是非空字符串")
        
        # 如果有sources，验证sources配置
        if 'sources' in self.config:
            sources = self.config['sources']
            if not isinstance(sources, list):
                raise ValueError("'sources'必须是一个列表")
            if len(sources) == 0:
                raise ValueError("'sources'不能为空（如果提供了sources字段）")
            for i, source in enumerate(sources):
                if not isinstance(source, dict):
                    raise ValueError(f"source[{i}]必须是一个字典")
                if 'source_name' not in source:
                    raise ValueError(f"source[{i}]缺少'source_name'")
                if 'lag_seconds' not in source:
                    raise ValueError(f"source[{i}]缺少'lag_seconds'")
                lag_seconds = source.get('lag_seconds', 0)
                if not isinstance(lag_seconds, (int, float)) or lag_seconds < 0:
                    raise ValueError(f"source[{i}]的'lag_seconds'必须是非负数")
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的数据名称列表"""
        if 'sources' in self.config:
            return [source['source_name'] for source in self.config['sources']]
        return []
    
    def generate(self, time_points: np.ndarray, 
                 other_data: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        生成数据
        
        流程：
        1. 判断是独立生成还是依赖生成
        2. 独立生成：构建变量字典（t）
        3. 依赖生成：处理sources（应用滞后），构建变量字典（x1, x2, x3）
        4. 执行表达式
        5. 添加噪声
        """
        expression = self.config['calculation']['expression']
        
        # 判断是独立生成还是依赖生成
        has_sources = 'sources' in self.config and len(self.config.get('sources', [])) > 0
        
        if has_sources:
            # 依赖生成模式
            sources = self.config['sources']
            
            if other_data is None:
                raise ValueError("依赖生成模式需要other_data参数")
            
            # 处理每个source（应用滞后）
            processed_sources = []
            for source in sources:
                source_name = source['source_name']
                lag_seconds = source.get('lag_seconds', 0)
                
                if source_name not in other_data:
                    raise ValueError(f"缺少依赖数据: {source_name}")
                raw_data = other_data[source_name]
                
                # 确保数据是numpy数组
                if not isinstance(raw_data, np.ndarray):
                    raw_data = np.array(raw_data)
                
                # 应用滞后
                if lag_seconds > 0:
                    processed_data = self._apply_lag(raw_data, time_points, lag_seconds)
                else:
                    processed_data = raw_data.copy()
                
                processed_sources.append(processed_data)
            
            # 构建变量字典（x1, x2, x3, ...）
            variables = {}
            for i, data in enumerate(processed_sources):
                variables[f'x{i+1}'] = data
            
            # 也提供时间变量（如果需要混合使用）
            variables['t'] = time_points
            
        else:
            # 独立生成模式
            # 构建变量字典（t）
            variables = {
                't': time_points,
            }
        
        # 添加数学函数和常量
        # 注意：函数需要在执行时动态生成，因为需要知道数组长度
        variables.update({
            'sqrt': np.sqrt,
            'log': np.log,
            'exp': np.exp,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'abs': np.abs,
            'max': np.maximum,
            'min': np.minimum,
            'power': np.power,
            'sign': np.sign,
            'pi': np.pi,
            'e': np.e,
        })
        
        # 执行表达式
        try:
            evaluator = SafeExpressionEvaluator()
            data = evaluator.evaluate(expression, variables)
            
            # 确保结果是numpy数组
            if not isinstance(data, np.ndarray):
                data = np.array(data)
            
            # 确保长度正确
            if len(data) != len(time_points):
                raise ValueError(f"表达式结果长度({len(data)})与时间点长度({len(time_points)})不匹配")
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"表达式计算错误: {str(e)}")
        
        # 添加噪声
        noise_level = self.config.get('noise_level', 0.0)
        if noise_level > 0:
            noise = np.random.normal(0, abs(data) * noise_level, size=len(data))
            data = data + noise
        
        return data
    
    def _apply_lag(self, data: np.ndarray, time_points: np.ndarray, lag_seconds: float) -> np.ndarray:
        """
        应用滞后
        
        Args:
            data: 原始数据数组
            time_points: 时间点数组（秒为单位的时间戳）
            lag_seconds: 滞后时间（秒）
        
        Returns:
            滞后后的数据数组
        
        说明：
            滞后意味着：output[i] = input[i - lag_points]
            例如：如果lag_seconds=30，time_interval=5，则lag_points=6
            那么 output[6] = input[0], output[7] = input[1], ...
            对于 i < lag_points 的情况，使用 input[0]
        """
        if len(time_points) < 2:
            # 如果只有一个时间点，无法计算时间间隔，直接返回
            return data.copy()
        
        time_interval = time_points[1] - time_points[0]
        if time_interval <= 0:
            # 时间间隔无效，直接返回
            return data.copy()
        
        lag_points = int(round(lag_seconds / time_interval))
        
        if lag_points == 0:
            # 无滞后，直接返回
            return data.copy()
        
        lagged_data = np.zeros_like(data)
        for i in range(len(data)):
            source_idx = i - lag_points
            if source_idx < 0:
                # 如果滞后索引小于0，使用源数据的第一个值
                source_idx = 0
            lagged_data[i] = data[source_idx]
        
        return lagged_data

