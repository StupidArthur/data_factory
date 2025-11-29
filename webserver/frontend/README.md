# 前端项目说明

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 请求封装
│   │   ├── index.js      # axios 实例配置
│   │   ├── groups.js     # 分组管理 API
│   │   ├── configs.js    # 配置管理 API
│   │   └── export.js     # 数据导出 API
│   ├── pages/            # 页面组件
│   │   ├── ConfigList.jsx    # 配置列表页
│   │   └── ConfigEdit.jsx    # 配置编辑页
│   ├── components/       # 公共组件（待添加）
│   ├── utils/            # 工具函数（待添加）
│   ├── styles/           # 样式文件
│   │   └── index.css     # 全局样式
│   ├── App.jsx           # 主应用组件（路由配置）
│   └── main.jsx          # 应用入口
├── package.json
└── vite.config.js        # Vite 配置（已配置 API 代理）
```

## 开发命令

### 启动开发服务器

```bash
npm run dev
```

开发服务器会在 `http://localhost:5173` 启动。

### 构建生产版本

```bash
npm run build
```

构建后的文件会输出到 `../static` 目录（覆盖旧的静态文件）。

### 预览生产构建

```bash
npm run preview
```

## 配置说明

### API 代理

在 `vite.config.js` 中已配置 API 代理，所有 `/api` 开头的请求会自动代理到 `http://localhost:8000`。

### 构建输出

构建后的文件会输出到 `webserver/static` 目录，这样后端可以直接服务这些文件。

## 开发流程

1. **启动后端服务器**（在 `webserver` 目录）：
   ```bash
   python app.py
   ```

2. **启动前端开发服务器**（在 `frontend` 目录）：
   ```bash
   npm run dev
   ```

3. **访问应用**：
   - 前端开发服务器：http://localhost:5173
   - 后端 API：http://localhost:8000

4. **开发调试**：
   - 修改代码后，浏览器会自动刷新（HMR）
   - 可以在浏览器开发者工具中设置断点
   - 使用 React DevTools 调试组件

## 技术栈

- **React 19.2.0** - UI 框架
- **Ant Design 6.0.0** - UI 组件库
- **React Router DOM 7.9.6** - 路由管理
- **Axios 1.13.2** - HTTP 客户端
- **Vite 7.2.4** - 构建工具

## 注意事项

1. 确保后端服务器（端口 8000）已启动，否则 API 请求会失败
2. 开发时使用前端开发服务器（端口 5173），不要直接访问后端
3. 生产部署时，先运行 `npm run build`，然后后端会自动服务构建后的文件
