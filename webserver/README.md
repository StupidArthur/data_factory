# 数据工厂 Web应用

基于Sanic + React + Ant Design的Web界面，提供模拟数据的组态、预览、导出功能。

## 功能特性

1. **配置管理（组态）**
   - 创建、编辑、删除YAML配置
   - 分组管理（创建、删除分组）
   - 配置列表管理（按分组筛选）

2. **数据导出**
   - 导出历史数据（10000点）
   - 导出完整数据（10120点，包含未来120点）
   - CSV格式下载

3. **配置存储**
   - SQLite数据库存储配置和分组
   - 支持配置的增删改查

## 技术栈

- **后端**: Sanic（异步Web框架）
- **数据库**: SQLite + SQLAlchemy
- **前端**: React 19 + Ant Design 6 + React Router + Axios
- **构建工具**: Vite
- **其他**: PyYAML, pandas, numpy

## 项目结构

```
webserver/
├── frontend/              # React 前端项目（开发）
│   ├── src/
│   │   ├── api/          # API 封装
│   │   ├── pages/        # 页面组件
│   │   ├── components/  # 公共组件
│   │   └── ...
│   └── package.json
├── static/               # 前端构建输出目录（生产）
├── api/                  # 后端API路由
├── models.py             # 数据库模型
└── app.py                # Sanic应用入口
```

## 安装依赖

### 后端依赖

```bash
pip install -r requirements.txt
```

### 前端依赖

```bash
cd frontend
npm install
```

## 开发模式

### 1. 启动后端服务器

```bash
cd webserver
python app.py
```

后端服务器运行在 `http://localhost:8000`

### 2. 启动前端开发服务器

```bash
cd webserver/frontend
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`

### 3. 访问应用

打开浏览器访问：`http://localhost:5173`

**注意**：开发时使用前端开发服务器（5173端口），不要直接访问后端（8000端口）。

## 生产部署

### 1. 构建前端

```bash
cd webserver/frontend
npm run build
```

构建后的文件会输出到 `webserver/static` 目录。

### 2. 启动后端服务器

```bash
cd webserver
python app.py
```

### 3. 访问应用

打开浏览器访问：`http://localhost:8000`

后端会自动服务构建后的前端文件。

## API接口

### 分组管理

- `GET /api/groups` - 获取分组列表
- `GET /api/groups/:id` - 获取单个分组
- `POST /api/groups` - 创建新分组
- `PUT /api/groups/:id` - 更新分组
- `DELETE /api/groups/:id` - 删除分组

### 配置管理

- `GET /api/configs` - 获取配置列表（支持 `?group_id=xxx` 参数）
- `GET /api/configs/:id` - 获取单个配置
- `POST /api/configs` - 创建新配置
- `PUT /api/configs/:id` - 更新配置
- `DELETE /api/configs/:id` - 删除配置

### 数据导出

- `GET /api/export/:id?type=history` - 导出历史数据
- `GET /api/export/:id?type=full` - 导出完整数据

## 使用说明

1. **创建分组**
   - 点击左侧"新建分组"按钮
   - 输入分组名称和描述
   - 点击"确定"

2. **创建配置**
   - 点击右上角"新建配置"按钮
   - 输入配置名称、选择分组、填写YAML配置
   - 点击"保存配置"

3. **编辑配置**
   - 在配置列表中点击"编辑"按钮
   - 修改配置内容
   - 点击"保存配置"

4. **导出数据**
   - 在配置列表中点击"导出数据"按钮
   - 会自动下载历史数据和完整数据两个CSV文件

5. **删除配置/分组**
   - 点击"删除"按钮
   - 确认删除操作

## 配置示例

```yaml
generator:
  time_interval: 5.0
  history_points: 10000
  future_points: 120
  start_time: "2024-01-01 00:00:00"
  
  templates:
    - type: TimePatternTemplate
      name: sine_wave
      config:
        output_name: F.sine
        pattern_type: sinusoidal
        amplitude: 100.0
        period: 3600.0
        phase: 0.0
        offset: 50.0
        noise_level: 0.05

template:
  time_format: datetime
  has_title_row: true
  has_description_row: true
  hide_parameter_descriptions: true
  column_descriptions:
    timeStamp: "时间戳"
    F.sine: "正弦波数据"
```

## 注意事项

1. 数据库文件（database.db）会自动创建在webserver目录下
2. 首次运行会自动创建"已删除"默认分组
3. 删除分组后，该分组下的配置会自动移动到"已删除"分组
4. 前端开发时，API请求会自动代理到后端（通过Vite配置）

## 开发说明

- **前端代码**: `webserver/frontend/src/` 目录
- **后端API**: `webserver/api/` 目录
- **数据库模型**: `webserver/models.py`
- **主应用入口**: `webserver/app.py`
- **前端构建输出**: `webserver/static/` 目录（构建后生成）

## 常见问题

### Q: 前端开发时API请求失败？
A: 确保后端服务器（8000端口）已启动，Vite会自动代理API请求。

### Q: 如何调试前端代码？
A: 使用浏览器开发者工具，可以设置断点、查看网络请求、使用React DevTools调试组件。

### Q: 生产环境如何部署？
A: 先运行 `npm run build` 构建前端，然后启动后端服务器即可。
