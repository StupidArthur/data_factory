"""
将旧的YAML配置文件转换为ExpressionTemplate格式
"""

import yaml
from pathlib import Path
import math

def convert_time_pattern_to_expression(template_config):
    """
    将TimePatternTemplate转换为ExpressionTemplate
    
    pattern_type: sinusoidal -> offset + amplitude * sin(2 * pi * t / period + phase)
    pattern_type: square -> offset + amplitude * sign(sin(2 * pi * t / period + phase))
    pattern_type: triangle -> 需要分段函数，比较复杂
    """
    pattern_type = template_config.get('pattern_type', 'sinusoidal')
    amplitude = template_config.get('amplitude', 0.0)
    period = template_config.get('period', 3600.0)
    phase = template_config.get('phase', 0.0)
    offset = template_config.get('offset', 0.0)
    noise_level = template_config.get('noise_level', 0.0)
    
    if pattern_type == 'sinusoidal':
        # 正弦波: offset + amplitude * sin(2 * pi * t / period + phase)
        # 注意：phase在TimePatternTemplate中可能是秒数（时间偏移）或度数（角度偏移）
        # 如果phase很大（> 1000），可能是秒数；否则是度数
        if abs(phase) > 1000:
            # phase是秒数，直接使用
            phase_rad = phase * 2 * math.pi / period  # 转换为弧度
        else:
            # phase是度数，转换为弧度
            phase_rad = phase * math.pi / 180.0
        expression = f"{offset} + {amplitude} * sin(2 * pi * t / {period} + {phase_rad})"
    elif pattern_type == 'square':
        # 方波: offset + amplitude * sign(sin(2 * pi * t / period + phase))
        phase_rad = phase * math.pi / 180.0
        expression = f"{offset} + {amplitude} * sign(sin(2 * pi * t / {period} + {phase_rad}))"
    elif pattern_type == 'triangle':
        # 三角波: 使用分段函数，比较复杂，这里用近似
        phase_rad = phase * math.pi / 180.0
        # 使用反正弦近似: offset + amplitude * (2/pi) * asin(sin(2 * pi * t / period + phase))
        expression = f"{offset} + {amplitude} * (2 / pi) * asin(sin(2 * pi * t / {period} + {phase_rad}))"
    else:
        # 默认正弦波
        phase_rad = phase * math.pi / 180.0
        expression = f"{offset} + {amplitude} * sin(2 * pi * t / {period} + {phase_rad})"
    
    return {
        'type': 'ExpressionTemplate',
        'name': template_config.get('name', 'template'),
        'config': {
            'output_name': template_config.get('output_name', 'F.output'),
            'calculation': {
                'expression': expression,
            },
            'noise_level': noise_level,
        }
    }

def convert_random_pattern_to_expression(template_config):
    """
    将RandomPatternTemplate转换为ExpressionTemplate
    
    distribution: uniform -> min_value + (max_value - min_value) * random()
    distribution: constrained_random_walk -> 这个比较复杂，需要特殊处理
    """
    distribution = template_config.get('distribution', 'uniform')
    min_value = template_config.get('min_value', 0.0)
    max_value = template_config.get('max_value', 100.0)
    noise_level = template_config.get('noise_level', 0.0)
    
    if distribution == 'uniform':
        # 均匀分布: min_value + (max_value - min_value) * random()
        expression = f"{min_value} + ({max_value} - {min_value}) * random()"
    elif distribution == 'constrained_random_walk':
        # 约束随机游走：这个比较复杂，需要状态变量
        # 由于表达式模板不支持状态变量，我们使用一个近似方法
        # 使用随机数加上一个平滑函数来模拟随机游走
        step_range = template_config.get('step_range', [-3.0, 3.0])
        step_min, step_max = step_range[0], step_range[1]
        # 使用随机数序列的累积和来模拟，但表达式模板不支持状态
        # 这里使用一个近似：使用多个随机数的组合
        # 注意：这不是真正的随机游走，但可以产生类似的效果
        expression = f"{min_value} + ({max_value} - {min_value}) * (0.5 + 0.1 * (random() - 0.5) * t / 86400)"
        # 更好的方法是使用多个随机数的加权平均
        # 但由于表达式模板的限制，我们使用这个近似
    else:
        # 默认均匀分布
        expression = f"{min_value} + ({max_value} - {min_value}) * random()"
    
    return {
        'type': 'ExpressionTemplate',
        'name': template_config.get('name', 'template'),
        'config': {
            'output_name': template_config.get('output_name', 'F.output'),
            'calculation': {
                'expression': expression,
            },
            'noise_level': noise_level,
        }
    }

def convert_lag_follow_to_expression(template_config, all_templates):
    """
    将LagFollowTemplate转换为ExpressionTemplate（依赖生成模式）
    
    LagFollowTemplate: result = initial_value + sensitivity * (source - initial_value) * exp(-decay_rate * t)
    但实际实现中，滞后跟随是直接使用滞后后的source值
    """
    source_name = template_config.get('source_name')
    lag_seconds = template_config.get('lag_seconds', 0)
    sensitivity = template_config.get('sensitivity', 1.0)
    initial_value = template_config.get('initial_value', 0.0)
    decay_rate = template_config.get('decay_rate', 0.0)
    noise_level = template_config.get('noise_level', 0.0)
    
    # 找到source在templates中的索引
    source_index = None
    for i, t in enumerate(all_templates):
        if t.get('config', {}).get('output_name') == source_name:
            source_index = i
            break
    
    if source_index is None:
        raise ValueError(f"找不到源参数: {source_name}")
    
    # 在依赖生成模式中，x1对应第一个source
    # 如果sensitivity=1.0且decay_rate=0.0，就是完全跟随
    if sensitivity == 1.0 and decay_rate == 0.0:
        expression = 'x1'
    else:
        # 需要考虑sensitivity和decay_rate
        # 但由于表达式模板的限制，我们简化处理
        if decay_rate == 0.0:
            expression = f"{initial_value} + {sensitivity} * (x1 - {initial_value})"
        else:
            # 衰减率比较复杂，这里简化处理
            expression = f"{initial_value} + {sensitivity} * (x1 - {initial_value}) * exp(-{decay_rate} * t / 3600)"
    
    return {
        'type': 'ExpressionTemplate',
        'name': template_config.get('name', 'template'),
        'config': {
            'output_name': template_config.get('output_name', 'F.output'),
            'sources': [
                {
                    'source_name': source_name,
                    'lag_seconds': lag_seconds,
                }
            ],
            'calculation': {
                'expression': expression,
            },
            'noise_level': noise_level,
        }
    }

def convert_polynomial_to_expression(template_config, all_templates):
    """
    将PolynomialTemplate转换为ExpressionTemplate（依赖生成模式）
    
    PolynomialTemplate: result = constant + sum(coefficient * source) + cross_terms
    """
    source_names = template_config.get('source_names', [])
    coefficients = template_config.get('coefficients', {})
    lag_seconds = template_config.get('lag_seconds', 0)  # PolynomialTemplate可能支持lag_seconds
    noise_level = template_config.get('noise_level', 0.0)
    
    # 构建表达式
    terms = []
    
    # 常数项
    constant = coefficients.get('constant', 0.0)
    if constant != 0.0:
        terms.append(str(constant))
    
    # 线性项
    for i, source_name in enumerate(source_names):
        var_name = f'x{i+1}'  # x1, x2, x3, ...
        coeff = coefficients.get(source_name, 0.0)
        if coeff != 0.0:
            if coeff == 1.0:
                terms.append(var_name)
            elif coeff == -1.0:
                terms.append(f'-{var_name}')
            else:
                terms.append(f'{coeff} * {var_name}')
    
    # 交叉项
    for key, coeff in coefficients.items():
        if key != 'constant' and key not in source_names and '*' in key:
            # 交叉项，如 F.x*F.y
            parts = key.split('*')
            if len(parts) == 2:
                source1, source2 = parts[0].strip(), parts[1].strip()
                # 找到source的索引
                idx1 = None
                idx2 = None
                for i, source_name in enumerate(source_names):
                    if source_name == source1:
                        idx1 = i
                    if source_name == source2:
                        idx2 = i
                
                if idx1 is not None and idx2 is not None:
                    var1 = f'x{idx1+1}'
                    var2 = f'x{idx2+1}'
                    if coeff != 0.0:
                        if coeff == 1.0:
                            terms.append(f'{var1} * {var2}')
                        elif coeff == -1.0:
                            terms.append(f'-{var1} * {var2}')
                        else:
                            terms.append(f'{coeff} * {var1} * {var2}')
    
    # 组合表达式
    if not terms:
        expression = '0'
    else:
        expression = ' + '.join(terms)
    
    # 构建sources列表（所有source使用相同的lag_seconds）
    sources = []
    for source_name in source_names:
        sources.append({
            'source_name': source_name,
            'lag_seconds': lag_seconds,
        })
    
    return {
        'type': 'ExpressionTemplate',
        'name': template_config.get('name', 'template'),
        'config': {
            'output_name': template_config.get('output_name', 'F.output'),
            'sources': sources,
            'calculation': {
                'expression': expression,
            },
            'noise_level': noise_level,
        }
    }

def convert_nonlinear_lag_to_expression(template_config, all_templates):
    """
    将NonlinearLagTemplate转换为ExpressionTemplate（依赖生成模式）
    
    NonlinearLagTemplate: 支持非线性函数（sqrt, log, exp等）和滞后
    """
    source_names = template_config.get('source_names', [])
    function = template_config.get('function', 'sqrt')
    function_params = template_config.get('function_params', {})
    lag_seconds = template_config.get('lag_seconds', 0)
    noise_level = template_config.get('noise_level', 0.0)
    
    # 构建表达式
    if function == 'sqrt':
        operation = function_params.get('operation', 'multiply')
        if operation == 'multiply':
            # sqrt(x1 * x2 * ...)
            if len(source_names) == 1:
                expression = f'sqrt(x1)'
            else:
                # 多个source相乘
                product_terms = [f'x{i+1}' for i in range(len(source_names))]
                expression = f'sqrt({" * ".join(product_terms)})'
        elif operation == 'add':
            # sqrt(x1 + x2 + ...)
            sum_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'sqrt({" + ".join(sum_terms)})'
        else:
            # 默认相乘
            product_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'sqrt({" * ".join(product_terms)})'
    elif function == 'log':
        # log(x1) 或 log(x1 + x2 + ...)
        if len(source_names) == 1:
            expression = f'log(x1)'
        else:
            sum_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'log({" + ".join(sum_terms)})'
    elif function == 'exp':
        # exp(x1) 或 exp(x1 + x2 + ...)
        if len(source_names) == 1:
            expression = f'exp(x1)'
        else:
            sum_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'exp({" + ".join(sum_terms)})'
    elif function == 'power':
        # power(x1, n) 或 power(x1 + x2, n)
        power = function_params.get('power', 2.0)
        if len(source_names) == 1:
            expression = f'power(x1, {power})'
        else:
            sum_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'power({" + ".join(sum_terms)}, {power})'
    else:
        # 默认sqrt
        if len(source_names) == 1:
            expression = f'sqrt(x1)'
        else:
            product_terms = [f'x{i+1}' for i in range(len(source_names))]
            expression = f'sqrt({" * ".join(product_terms)})'
    
    # 构建sources列表（所有source使用相同的lag_seconds）
    sources = []
    for source_name in source_names:
        sources.append({
            'source_name': source_name,
            'lag_seconds': lag_seconds,
        })
    
    return {
        'type': 'ExpressionTemplate',
        'name': template_config.get('name', 'template'),
        'config': {
            'output_name': template_config.get('output_name', 'F.output'),
            'sources': sources,
            'calculation': {
                'expression': expression,
            },
            'noise_level': noise_level,
        }
    }

def convert_config_file(input_path, output_path):
    """
    转换单个配置文件
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if 'generator' not in config or 'templates' not in config['generator']:
        print(f"跳过 {input_path.name}：没有templates配置")
        return False
    
    templates = config['generator']['templates']
    new_templates = []
    
    # 第一遍：转换所有独立生成的模板（TimePatternTemplate, RandomPatternTemplate）
    for template in templates:
        template_type = template.get('type')
        template_config = template.get('config', {})
        
        if template_type == 'TimePatternTemplate':
            new_template = convert_time_pattern_to_expression(template_config)
            new_template['name'] = template.get('name', 'template')
            new_templates.append(new_template)
        elif template_type == 'RandomPatternTemplate':
            new_template = convert_random_pattern_to_expression(template_config)
            new_template['name'] = template.get('name', 'template')
            new_templates.append(new_template)
        elif template_type in ['LagFollowTemplate', 'PolynomialTemplate', 'NonlinearLagTemplate']:
            # 这些需要依赖其他模板，先跳过，第二遍处理
            new_templates.append(template)
        else:
            # 其他类型暂时保留原样
            print(f"警告：未知的模板类型 {template_type}，保留原样")
            new_templates.append(template)
    
    # 第二遍：转换依赖生成的模板（LagFollowTemplate, PolynomialTemplate）
    final_templates = []
    for template in new_templates:
        template_type = template.get('type')
        template_config = template.get('config', {})
        
        if template_type == 'LagFollowTemplate':
            new_template = convert_lag_follow_to_expression(template_config, new_templates)
            new_template['name'] = template.get('name', 'template')
            final_templates.append(new_template)
        elif template_type == 'PolynomialTemplate':
            new_template = convert_polynomial_to_expression(template_config, new_templates)
            new_template['name'] = template.get('name', 'template')
            final_templates.append(new_template)
        elif template_type == 'NonlinearLagTemplate':
            new_template = convert_nonlinear_lag_to_expression(template_config, new_templates)
            new_template['name'] = template.get('name', 'template')
            final_templates.append(new_template)
        else:
            final_templates.append(template)
    
    # 更新配置
    config['generator']['templates'] = final_templates
    
    # 保存到输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    return True

def main():
    """
    主函数：转换config目录下的所有yaml文件
    """
    config_dir = Path('config')
    output_dir = Path('input')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    yaml_files = list(config_dir.glob('*.yaml')) + list(config_dir.glob('*.yml'))
    
    for yaml_file in yaml_files:
        if yaml_file.name in ['example_config.yaml']:
            continue  # 跳过示例文件
        
        output_file = output_dir / yaml_file.name
        print(f"转换: {yaml_file.name} -> {output_file.name}")
        
        try:
            success = convert_config_file(yaml_file, output_file)
            if success:
                print(f"  ✓ 成功")
            else:
                print(f"  ✗ 跳过")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n转换完成！输出目录: {output_dir}")

if __name__ == '__main__':
    main()

