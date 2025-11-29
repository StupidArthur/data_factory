/**
 * 模板库组件 - 显示可拖拽的模板类型
 */

import { useState } from 'react'
import { Card } from 'antd'
import { DragOutlined } from '@ant-design/icons'

const TEMPLATE_LIBRARY = [
  {
    type: 'ExpressionTemplate',
    name: '表达式模板',
    description: '使用Python表达式生成数据，支持独立生成和依赖生成',
    icon: '🔧',
    detail: `表达式模板是完全统一的表达式模板，支持独立生成和依赖生成两种模式。

主要特点：
• 独立生成：表达式使用 t（时间）作为变量
• 依赖生成：表达式使用 x1, x2, x3（其他位号）作为变量
• 支持常用数学函数和运算符
• 支持滞后配置（每个位号独立配置）
• 灵活强大，支持任意表达式组合

独立生成示例：
- 常数: '50'
- 正弦波: '50 + 100 * sin(2 * pi * t / 86400)'
- 方波: '50 + 100 * sign(sin(2 * pi * t / 86400))'
- 随机数: '50 + random() * 100'
- 线性趋势: '50 + t * 0.001'
- 指数趋势: '50 * exp(t * 0.00001)'

依赖生成示例：
- 线性组合: 'x1 * 0.5 + x2 * 0.3 + 10'
- 带函数: 'sin(x1) + sqrt(x2) + log(x3 + 1)'
- 混合时间和位号: 'x1 * 0.5 + sin(2 * pi * t / 86400) * 10'
- 多项式（带交叉项）: '10 + x1 * 2.0 + x2 * 3.0 + x1 * x2 * 0.1'

支持的函数：
sqrt, log, exp, sin, cos, tan, abs, max, min, power, sign, random, random_normal

支持的常量：
pi（圆周率）, e（自然常数）

支持的运算符：
+, -, *, /, **（幂）, %（取模）`,
  },
]

function TemplateLibrary() {
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  const handleDragStart = (e, template) => {
    e.dataTransfer.effectAllowed = 'copy'
    e.dataTransfer.setData('application/json', JSON.stringify({
      type: 'template-library',
      templateType: template.type,
    }))
  }

  const handleCardClick = (template) => {
    setSelectedTemplate(template)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ 
        marginBottom: 12, 
        fontWeight: 600,
        fontSize: '15px',
        color: '#1890ff',
        padding: '8px 12px',
        backgroundColor: '#e6f7ff',
        border: '1px solid #91d5ff',
        borderRadius: '4px',
        height: '40px',
        display: 'flex',
        alignItems: 'center',
      }}>
        模板库
      </div>

      {/* 详情展示区 */}
      <div style={{
        marginBottom: 12,
        minHeight: '240px',
        maxHeight: '240px',
        border: '1px solid #d9d9d9',
        borderRadius: '4px',
        backgroundColor: '#fafafa',
        padding: '12px',
        overflowY: 'auto',
      }}>
        {selectedTemplate ? (
          <div>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8, 
              marginBottom: 12,
              fontSize: '16px',
              fontWeight: 600,
            }}>
              <span style={{ fontSize: '20px' }}>{selectedTemplate.icon}</span>
              <span>{selectedTemplate.name}</span>
            </div>
            <div style={{ 
              fontSize: '12px', 
              color: '#666',
              lineHeight: '1.6',
              whiteSpace: 'pre-line',
            }}>
              {selectedTemplate.detail}
            </div>
          </div>
        ) : (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            height: '100%',
            color: '#999',
            fontSize: '13px',
          }}>
            点击下方模板查看详细信息
          </div>
        )}
      </div>

      {/* 模板列表 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto' }}>
        {TEMPLATE_LIBRARY.map((template) => (
          <Card
            key={template.type}
            size="small"
            draggable
            onDragStart={(e) => handleDragStart(e, template)}
            onClick={() => handleCardClick(template)}
            style={{
              cursor: 'pointer',
              userSelect: 'none',
              borderColor: selectedTemplate?.type === template.type ? '#1890ff' : undefined,
              borderWidth: selectedTemplate?.type === template.type ? '2px' : undefined,
            }}
            bodyStyle={{ padding: '12px' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <DragOutlined style={{ color: '#999' }} />
              <span style={{ fontSize: '18px', marginRight: 8 }}>{template.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: '13px' }}>{template.name}</div>
                <div style={{ fontSize: '11px', color: '#999', marginTop: 4 }}>
                  {template.description}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default TemplateLibrary

