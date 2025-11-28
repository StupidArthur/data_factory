# 数据工厂 (Data Factory)

工业数据生成、管理和可视化系统，用于测试工业大模型的预测能力。

## 功能特性

- 🎯 **能力模板系统**: 插件化架构，支持自定义数据生成能力
- 📊 **多种数据关系**: 时间规律、滞后跟随、多项式关系等
- 🔧 **灵活配置**: 所有参数均可配置
- 📈 **数据可视化**: PyQt6实现的交互式数据查看工具
- 📝 **模板管理**: 支持多种CSV输出格式和时间格式
- 📦 **模块化设计**: 清晰的代码结构，易于扩展

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 使用示例

生成数据：
```bash
python main.py --config config/example_config.json --output output/data.csv
```

预览数据：
```bash
python main.py --config config/example_config.json --preview
```

## 项目结构

```
data_factory/
├── core/              # 核心数据生成逻辑
│   ├── generators/    # 数据生成器
│   └── relationships/ # 能力模板（数据关系）
├── template/          # 模板管理模块
├── output/            # 数据输出模块
├── visualization/     # 可视化工具
├── utils/             # 工具函数（日志等）
├── config/            # 配置文件
├── doc/               # 项目文档
└── main.py            # 主程序入口
```

## 文档

- [需求文档](doc/需求文档.md)
- [设计文档](doc/设计文档.md)
- [用户手册](doc/用户手册.md)
- [交互记录](doc/interaction_record.md)

## 能力模板

系统支持以下能力模板：

1. **TimePatternTemplate**: 时间规律变化（正弦、线性、指数）
2. **LagFollowTemplate**: 滞后线性跟随
3. **PolynomialTemplate**: 多项式关系
4. **CompositeCapabilityTemplate**: 组合能力模板

## 技术栈

- Python 3.13
- pandas
- scipy
- PyQt6
- pyqtgraph

## 许可证

MIT License
