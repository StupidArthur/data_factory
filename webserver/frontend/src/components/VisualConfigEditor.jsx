/**
 * 图形化配置编辑器组件
 */

import { useState, useEffect } from 'react'
import {
  Card,
  Input,
  InputNumber,
  DatePicker,
  Button,
  Space,
  Form,
  Select,
  Divider,
  message,
  Row,
  Col,
  Radio,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  DragOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { parseYamlConfig, generateYamlConfig } from '../utils/yamlParser'
import TemplateLibrary from './TemplateLibrary'

const { TextArea } = Input

/**
 * 表达式模板配置字段组件
 */
function ExpressionTemplateFields({ form, availableOutputs }) {
  const [isDependent, setIsDependent] = useState(false)
  const [sources, setSources] = useState([])
  const [showFunctions, setShowFunctions] = useState(false)
  
  // 支持的函数列表
  const supportedFunctions = [
    { name: 'sqrt', desc: '平方根', example: 'sqrt(x)' },
    { name: 'log', desc: '自然对数', example: 'log(x)' },
    { name: 'exp', desc: '指数函数', example: 'exp(x)' },
    { name: 'sin', desc: '正弦', example: 'sin(x)' },
    { name: 'cos', desc: '余弦', example: 'cos(x)' },
    { name: 'tan', desc: '正切', example: 'tan(x)' },
    { name: 'abs', desc: '绝对值', example: 'abs(x)' },
    { name: 'max', desc: '最大值', example: 'max(x1, x2)' },
    { name: 'min', desc: '最小值', example: 'min(x1, x2)' },
    { name: 'power', desc: '幂函数', example: 'power(x, 2)' },
    { name: 'sign', desc: '符号函数', example: 'sign(x)' },
    { name: 'random', desc: '随机数(0-1)', example: 'random()' },
    { name: 'random_normal', desc: '正态分布随机数', example: 'random_normal(0, 1)' },
  ]
  
  // 常量
  const constants = [
    { name: 'pi', desc: '圆周率', value: '3.14159...' },
    { name: 'e', desc: '自然常数', value: '2.71828...' },
  ]
  
  // 监听is_dependent字段变化
  useEffect(() => {
    const subscription = form.getFieldValue('is_dependent')
    if (subscription !== undefined) {
      setIsDependent(subscription)
    }
  }, [form])
  
  // 监听sources字段变化
  useEffect(() => {
    const currentSources = form.getFieldValue('sources') || []
    setSources(currentSources)
  }, [form])
  
  const handleModeChange = (e) => {
    const newIsDependent = e.target.value === 'dependent'
    setIsDependent(newIsDependent)
    form.setFieldsValue({ is_dependent: newIsDependent })
    if (!newIsDependent) {
      form.setFieldsValue({ sources: [] })
      setSources([])
    }
  }
  
  const handleAddSource = () => {
    const newSources = [...sources, { source_name: '', lag_seconds: 0 }]
    setSources(newSources)
    form.setFieldsValue({ sources: newSources })
  }
  
  const handleSourceChange = (index, field, value) => {
    const newSources = [...sources]
    newSources[index] = { ...newSources[index], [field]: value }
    setSources(newSources)
    form.setFieldsValue({ sources: newSources })
  }
  
  const handleDeleteSource = (index) => {
    const newSources = sources.filter((_, i) => i !== index)
    setSources(newSources)
    form.setFieldsValue({ sources: newSources })
  }
  
  return (
    <>
      <Form.Item
        name="output_name"
        label="输出名称"
        rules={[{ required: true, message: '请输入输出名称' }]}
      >
        <Input placeholder="如: F.expression" />
      </Form.Item>
      
      <Form.Item
        name="is_dependent"
        label="生成模式"
        initialValue={false}
      >
        <Radio.Group onChange={handleModeChange}>
          <Radio value={false}>独立生成（使用时间 t）</Radio>
          <Radio value={true}>依赖生成（使用位号 x1, x2, ...）</Radio>
        </Radio.Group>
      </Form.Item>
      
      {isDependent && (
        <Form.Item
          name="sources"
          label="依赖位号列表"
          rules={[{ required: true, message: '请至少添加一个依赖位号' }]}
        >
          <div>
            <Button 
              type="dashed" 
              onClick={handleAddSource}
              style={{ marginBottom: 8, width: '100%' }}
            >
              + 添加位号
            </Button>
            {sources.map((source, index) => (
              <Card 
                key={index} 
                size="small" 
                style={{ marginBottom: 8 }}
                extra={
                  <Button 
                    type="link" 
                    danger 
                    size="small"
                    onClick={() => handleDeleteSource(index)}
                  >
                    删除
                  </Button>
                }
              >
                <Row gutter={8}>
                  <Col span={14}>
                    <Form.Item
                      name={['sources', index, 'source_name']}
                      rules={[{ required: true, message: '请选择位号' }]}
                      style={{ marginBottom: 8 }}
                    >
                      <Select placeholder="选择位号">
                        {availableOutputs.map((output) => (
                          <Select.Option key={output} value={output}>
                            {output}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={10}>
                    <Form.Item
                      name={['sources', index, 'lag_seconds']}
                      rules={[{ required: true, message: '请输入滞后时间' }]}
                      style={{ marginBottom: 8 }}
                    >
                      <InputNumber
                        placeholder="滞后时间（秒）"
                        min={0}
                        style={{ width: '100%' }}
                        addonAfter="秒"
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            ))}
          </div>
        </Form.Item>
      )}
      
      <Form.Item
        name="expression"
        label="计算表达式"
        rules={[{ required: true, message: '请输入表达式' }]}
      >
        <div>
          <Space style={{ marginBottom: 8 }}>
            <Button 
              type="link" 
              size="small" 
              onClick={() => setShowFunctions(!showFunctions)}
            >
              {showFunctions ? '隐藏' : '显示'}支持的函数和常量
            </Button>
          </Space>
          
          {showFunctions && (
            <Card size="small" style={{ marginBottom: 8 }}>
              <div style={{ fontSize: '12px' }}>
                <div style={{ marginBottom: 8, fontWeight: 'bold' }}>支持的函数：</div>
                <Row gutter={[8, 8]}>
                  {supportedFunctions.map(func => (
                    <Col span={8} key={func.name}>
                      <Space>
                        <code>{func.name}</code>
                        <span style={{ color: '#666' }}>{func.desc}</span>
                      </Space>
                    </Col>
                  ))}
                </Row>
                <div style={{ marginTop: 8, marginBottom: 8, fontWeight: 'bold' }}>常量：</div>
                <Row gutter={[8, 8]}>
                  {constants.map(constant => (
                    <Col span={8} key={constant.name}>
                      <Space>
                        <code>{constant.name}</code>
                        <span style={{ color: '#666' }}>{constant.desc}</span>
                      </Space>
                    </Col>
                  ))}
                </Row>
              </div>
            </Card>
          )}
          
          <TextArea
            rows={4}
            placeholder={
              isDependent 
                ? "例如: x1 * 0.5 + sin(x2) + sqrt(x3) + 10"
                : "例如: 50 + 100 * sin(2 * pi * t / 86400)"
            }
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
          
          <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
            {isDependent ? (
              <>
                <div>变量说明：</div>
                <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                  {sources.map((source, index) => (
                    <li key={index}>
                      <code>x{index + 1}</code> = {source.source_name || '未选择'} 
                      {source.lag_seconds > 0 && ` (滞后${source.lag_seconds}秒)`}
                    </li>
                  ))}
                </ul>
                <div>也可以使用 <code>t</code> 表示时间（秒）</div>
              </>
            ) : (
              <div>变量说明：<code>t</code> 表示时间（秒），从start_time开始计算</div>
            )}
            <div>运算符：+, -, *, /, **（幂）, %（取模）</div>
          </div>
        </div>
      </Form.Item>
      
      <Form.Item name="noise_level" label="噪声水平">
        <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.01} />
      </Form.Item>
    </>
  )
}

/**
 * 模板类型配置
 */
const TEMPLATE_TYPES = [
  { value: 'ExpressionTemplate', label: '表达式模板' },
]

/**
 * 模板类型中文名称映射
 */
const TEMPLATE_TYPE_NAMES = {
  'ExpressionTemplate': '表达式模板',
}

/**
 * 模板卡片组件
 */
function TemplateCard({ template, index, onUpdate, onDelete, availableOutputs, onDragStart, onDragOver, onDrop, isDragging, columnDescriptions }) {
  const [editing, setEditing] = useState(false)
  const [form] = Form.useForm()
  
  // 获取参数描述
  const getParameterDescription = () => {
    const outputName = template.config?.output_name
    if (outputName && columnDescriptions && columnDescriptions[outputName]) {
      return columnDescriptions[outputName]
    }
    return '无描述'
  }
  
  // 获取模板类型中文名称
  const getTemplateTypeName = () => {
    return TEMPLATE_TYPE_NAMES[template.type] || template.type
  }
  
  // 渲染配置参数信息
  const renderConfigParams = () => {
    const config = template.config || {}
    
    if (template.type === 'TimePatternTemplate') {
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px', fontSize: '11px', color: '#666' }}>
          <div>模式: <span style={{ color: '#333' }}>{config.pattern_type || '-'}</span></div>
          <div>振幅: <span style={{ color: '#333' }}>{config.amplitude ?? '-'}</span></div>
          <div>周期: <span style={{ color: '#333' }}>{config.period ? `${config.period}秒` : '-'}</span></div>
          <div>相位: <span style={{ color: '#333' }}>{config.phase ? `${config.phase}秒` : '-'}</span></div>
          <div>偏移量: <span style={{ color: '#333' }}>{config.offset ?? '-'}</span></div>
          <div>噪声: <span style={{ color: '#333' }}>{config.noise_level ?? '-'}</span></div>
        </div>
      )
    } else if (template.type === 'LagFollowTemplate') {
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px', fontSize: '11px', color: '#666' }}>
          <div>源参数: <span style={{ color: '#333' }}>{config.source_name || '-'}</span></div>
          <div>滞后: <span style={{ color: '#333' }}>{config.lag_seconds ? `${config.lag_seconds}秒` : '-'}</span></div>
          <div>敏感度: <span style={{ color: '#333' }}>{config.sensitivity ?? '-'}</span></div>
          <div>初始值: <span style={{ color: '#333' }}>{config.initial_value ?? '-'}</span></div>
          <div>衰减率: <span style={{ color: '#333' }}>{config.decay_rate ?? '-'}</span></div>
          <div>噪声: <span style={{ color: '#333' }}>{config.noise_level ?? '-'}</span></div>
        </div>
      )
    } else if (template.type === 'PolynomialTemplate') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '11px', color: '#666' }}>
          <div>源参数: <span style={{ color: '#333' }}>{config.source_names?.length ? config.source_names.join(', ') : '-'}</span></div>
          <div>系数: <span style={{ color: '#333' }}>{config.coefficients ? JSON.stringify(config.coefficients).substring(0, 50) + '...' : '-'}</span></div>
          <div>噪声: <span style={{ color: '#333' }}>{config.noise_level ?? '-'}</span></div>
        </div>
      )
    } else if (template.type === 'ExpressionTemplate') {
      const expression = config.calculation?.expression || '-'
      const sources = config.sources || []
      const isDependent = sources.length > 0
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '11px', color: '#666' }}>
          <div>模式: <span style={{ color: '#333' }}>{isDependent ? '依赖生成' : '独立生成'}</span></div>
          {isDependent && (
            <div>依赖位号: <span style={{ color: '#333' }}>{sources.length}个</span></div>
          )}
          <div>表达式: <span style={{ color: '#333', fontFamily: 'monospace', fontSize: '10px' }}>{expression.length > 50 ? expression.substring(0, 50) + '...' : expression}</span></div>
          <div>噪声: <span style={{ color: '#333' }}>{config.noise_level ?? '-'}</span></div>
        </div>
      )
    }
    return null
  }

  useEffect(() => {
    if (template) {
      const formValues = {
        type: template.type,
        name: template.name,
        ...template.config,
      }
      // 处理PolynomialTemplate的coefficients字段（可能是对象，需要转换为JSON字符串）
      if (template.type === 'PolynomialTemplate' && template.config?.coefficients) {
        if (typeof template.config.coefficients === 'object') {
          formValues.coefficients = JSON.stringify(template.config.coefficients, null, 2)
        }
      }
      // 处理ExpressionTemplate的calculation字段
      if (template.type === 'ExpressionTemplate' && template.config?.calculation) {
        formValues.expression = template.config.calculation.expression || ''
        formValues.sources = template.config.sources || []
        formValues.is_dependent = (template.config.sources || []).length > 0
      }
      form.setFieldsValue(formValues)
    }
  }, [template, form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      const { type, name, coefficients, expression, sources, is_dependent, ...config } = values
      // 处理PolynomialTemplate的coefficients字段（JSON字符串转对象）
      if (type === 'PolynomialTemplate' && coefficients) {
        try {
          config.coefficients = JSON.parse(coefficients)
        } catch (e) {
          message.error('系数配置格式错误，请输入有效的JSON格式')
          return
        }
      }
      // 处理ExpressionTemplate的calculation和sources字段
      if (type === 'ExpressionTemplate') {
        config.calculation = {
          expression: expression || '',
        }
        if (is_dependent && sources && sources.length > 0) {
          config.sources = sources
        } else {
          // 独立生成模式，不包含sources字段
          delete config.sources
        }
      }
      onUpdate(index, {
        type,
        name,
        config,
      })
      setEditing(false)
    })
  }

  const renderConfigFields = () => {
    const type = form.getFieldValue('type')
    
    if (type === 'TimePatternTemplate') {
      return (
        <>
          <Form.Item
            name="output_name"
            label="输出名称"
            rules={[{ required: true, message: '请输入输出名称' }]}
          >
            <Input placeholder="如: F.sine" />
          </Form.Item>
          <Form.Item
            name="pattern_type"
            label="模式类型"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="sinusoidal">正弦波</Select.Option>
              <Select.Option value="square">方波</Select.Option>
              <Select.Option value="triangle">三角波</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="amplitude" label="振幅">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="period" label="周期（秒）">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="phase" label="相位（秒）">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="offset" label="偏移量">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="noise_level" label="噪声水平">
            <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.01} />
          </Form.Item>
        </>
      )
    } else if (type === 'LagFollowTemplate') {
      return (
        <>
          <Form.Item
            name="output_name"
            label="输出名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: F.temperature" />
          </Form.Item>
          <Form.Item
            name="source_name"
            label="源参数"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择源参数">
              {availableOutputs.map((output) => (
                <Select.Option key={output} value={output}>
                  {output}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="lag_seconds" label="滞后时间（秒）">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="sensitivity" label="敏感度">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="initial_value" label="初始值">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="decay_rate" label="衰减率">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="noise_level" label="噪声水平">
            <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.01} />
          </Form.Item>
        </>
      )
    } else if (type === 'PolynomialTemplate') {
      return (
        <>
          <Form.Item
            name="output_name"
            label="输出名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: F.combined" />
          </Form.Item>
          <Form.Item
            name="source_names"
            label="源参数列表"
            rules={[{ required: true }]}
          >
            <Select mode="multiple" placeholder="选择源参数">
              {availableOutputs.map((output) => (
                <Select.Option key={output} value={output}>
                  {output}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="coefficients" label="系数配置">
            <TextArea
              rows={4}
              placeholder='格式: {"constant": 10.0, "F.light": 0.1, "F.power": 0.2}'
            />
          </Form.Item>
          <Form.Item name="noise_level" label="噪声水平">
            <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.01} />
          </Form.Item>
        </>
      )
    } else if (type === 'ExpressionTemplate') {
      return <ExpressionTemplateFields form={form} availableOutputs={availableOutputs} />
    }
    return null
  }

  const handleCardDragStart = (e) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('application/json', JSON.stringify({
      type: 'template-item',
      index,
    }))
    if (onDragStart) onDragStart(index)
  }

  const handleCardDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // 检查拖拽类型（在onDragOver中无法使用getData，但可以检查types）
    if (e.dataTransfer.types.includes('application/json')) {
      e.dataTransfer.dropEffect = 'copy'
    } else {
      e.dataTransfer.dropEffect = 'move'
    }
    if (onDragOver) onDragOver(e, index)
  }

  const handleCardDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (onDrop) onDrop(e, index)
  }

  if (!editing) {
    return (
      <div
        draggable
        onDragStart={handleCardDragStart}
        onDragOver={handleCardDragOver}
        onDrop={handleCardDrop}
        style={{
          marginBottom: 12,
          opacity: isDragging ? 0.5 : 1,
          cursor: 'move',
        }}
      >
        <Card
          size="small"
          bodyStyle={{ padding: '12px' }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
            {/* 左侧：参数信息 */}
            <div style={{ flex: '0 0 auto', minWidth: '180px', display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <DragOutlined style={{ color: '#999', cursor: 'move', fontSize: '14px' }} />
                <span style={{ fontSize: '13px', fontWeight: 500, color: '#1890ff' }}>
                  [{index + 1}] {template.config?.output_name || '-'}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginLeft: '22px' }}>
                {getParameterDescription()}
              </div>
              <div style={{ fontSize: '11px', color: '#999', marginLeft: '22px' }}>
                {getTemplateTypeName()}
              </div>
            </div>
            
            {/* 中间：配置参数信息 */}
            <div style={{ 
              flex: 1, 
              minWidth: 0,
              margin: '0 auto',
              padding: '8px 12px',
              backgroundColor: '#f5f5f5',
              border: '1px solid #e8e8e8',
              borderRadius: '6px',
            }}>
              {renderConfigParams()}
            </div>
            
            {/* 右侧：操作按钮 */}
            <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  setEditing(true)
                }}
              >
                编辑
              </Button>
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(index)
                }}
              >
                删除
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <Card
      size="small"
      title="编辑模板"
      extra={
        <Space>
          <Button size="small" onClick={() => setEditing(false)}>
            取消
          </Button>
          <Button size="small" type="primary" onClick={handleSave}>
            保存
          </Button>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="type"
          label="模板类型"
          rules={[{ required: true }]}
          initialValue="ExpressionTemplate"
        >
          <Select disabled>
            {TEMPLATE_TYPES.map((type) => (
              <Select.Option key={type.value} value={type.value}>
                {type.label}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item
          name="name"
          label="模板名称"
          rules={[{ required: true }]}
        >
          <Input placeholder="如: sine_wave" />
        </Form.Item>
        {renderConfigFields()}
      </Form>
    </Card>
  )
}

/**
 * 图形化配置编辑器主组件
 */
function VisualConfigEditor({ yamlConfig, onChange, showOnlyBaseParams = false, showOnlyTemplates = false }) {
  const [config, setConfig] = useState(null)
  const [baseForm] = Form.useForm()
  // 将拖拽相关的state移到顶层，避免Hooks顺序问题
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)

  // 同步配置到YAML（使用防抖避免频繁更新）
  const syncToYaml = (configToSync) => {
    if (!configToSync) {
      return
    }
    try {
      const result = generateYamlConfig(configToSync)
      if (result.success && result.data) {
        // 只在生成成功且内容不同时才调用onChange，避免循环更新
        onChange(result.data)
      } else {
        console.error('生成YAML失败: ' + (result.error || '未知错误'))
        // 不显示错误消息，避免频繁弹窗
      }
    } catch (error) {
      console.error('生成YAML异常: ', error)
    }
  }

  // 解析YAML配置（使用useMemo避免频繁解析）
  useEffect(() => {
    if (!yamlConfig) {
      // 如果yamlConfig为空，保留现有config，不设置为null
      console.log('VisualConfigEditor: yamlConfig为空')
      return
    }

    console.log('VisualConfigEditor: 开始解析YAML，长度:', yamlConfig.length)
    try {
      const result = parseYamlConfig(yamlConfig)
      console.log('VisualConfigEditor: YAML解析结果:', result)
      
      if (result.success && result.data) {
        const parsedConfig = result.data
        console.log('VisualConfigEditor: 解析成功，config:', parsedConfig)
        
        // 确保config有generator字段
        if (!parsedConfig.generator) {
          console.warn('VisualConfigEditor: 解析的配置缺少generator字段')
          parsedConfig.generator = {
            time_interval: 5.0,
            history_points: 10000,
            future_points: 120,
            start_time: '2024-01-01 00:00:00',
            templates: [],
          }
        }
        
        // 只在解析成功时更新config
        setConfig(parsedConfig)
        
        // 设置基础参数表单（只在值变化时更新）
        if (parsedConfig.generator) {
          const newValues = {
            time_interval: parsedConfig.generator.time_interval,
            history_points: parsedConfig.generator.history_points,
            future_points: parsedConfig.generator.future_points,
            start_time: parsedConfig.generator.start_time
              ? dayjs(parsedConfig.generator.start_time, 'YYYY-MM-DD HH:mm:ss')
              : null,
          }
          
          // 只在值真正变化时更新表单
          const currentValues = baseForm.getFieldsValue()
          const valuesChanged = 
            currentValues.time_interval !== newValues.time_interval ||
            currentValues.history_points !== newValues.history_points ||
            currentValues.future_points !== newValues.future_points ||
            (currentValues.start_time?.format('YYYY-MM-DD HH:mm:ss') !== 
             newValues.start_time?.format('YYYY-MM-DD HH:mm:ss'))
          
          if (valuesChanged) {
            baseForm.setFieldsValue(newValues)
          }
        }
        
        // 确保生成的YAML格式正确，同步到父组件
        setTimeout(() => {
          syncToYaml(parsedConfig)
        }, 0)
      } else {
        console.error('VisualConfigEditor: YAML解析失败:', result.error)
        // YAML解析失败时，保留现有config，不设置为null
        // 但如果config也为null，则创建一个默认配置
        if (!config) {
          console.log('VisualConfigEditor: 创建默认配置')
          const defaultConfig = {
            generator: {
              time_interval: 5.0,
              history_points: 10000,
              future_points: 120,
              start_time: '2024-01-01 00:00:00',
              templates: [],
            },
            template: {
              time_format: 'datetime',
              has_title_row: true,
              has_description_row: true,
              hide_parameter_descriptions: true,
              column_descriptions: {},
            },
          }
          setConfig(defaultConfig)
        }
      }
    } catch (error) {
      console.error('VisualConfigEditor: YAML解析异常:', error)
      // 解析异常时，保留现有config，不设置为null
      // 但如果config也为null，则创建一个默认配置
      if (!config) {
        console.log('VisualConfigEditor: 创建默认配置（异常情况）')
        const defaultConfig = {
          generator: {
            time_interval: 5.0,
            history_points: 10000,
            future_points: 120,
            start_time: '2024-01-01 00:00:00',
            templates: [],
          },
          template: {
            time_format: 'datetime',
            has_title_row: true,
            has_description_row: true,
            hide_parameter_descriptions: true,
            column_descriptions: {},
          },
        }
        setConfig(defaultConfig)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yamlConfig])

  // 获取所有可用的输出名称
  const getAvailableOutputs = () => {
    if (!config?.generator?.templates) return []
    return config.generator.templates
      .map((t) => t.config?.output_name)
      .filter(Boolean)
  }

  // 更新配置并同步到YAML
  const updateConfig = (updates) => {
    const newConfig = {
      ...config,
      generator: {
        ...config.generator,
        ...updates.generator,
      },
      template: {
        ...config.template,
        ...updates.template,
      },
    }
    setConfig(newConfig)
    syncToYaml(newConfig)
  }

  // 处理基础参数变化
  const handleBaseChange = () => {
    const values = baseForm.getFieldsValue()
    updateConfig({
      generator: {
        ...config.generator,
        time_interval: values.time_interval,
        history_points: values.history_points,
        future_points: values.future_points,
        start_time: values.start_time
          ? values.start_time.format('YYYY-MM-DD HH:mm:ss')
          : config.generator.start_time,
      },
    })
  }

  // 添加模板
  const handleAddTemplate = () => {
    const newTemplate = {
      type: 'ExpressionTemplate',
      name: `template_${Date.now()}`,
      config: {
        output_name: `F.template_${Date.now()}`,
        calculation: {
          expression: '50 + 100 * sin(2 * pi * t / 86400)',
        },
        noise_level: 0.05,
      },
    }
    const newConfig = {
      ...config,
      generator: {
        ...config.generator,
        templates: [...(config.generator.templates || []), newTemplate],
      },
    }
    setConfig(newConfig)
    syncToYaml(newConfig)
  }

  // 更新模板
  const handleUpdateTemplate = (index, template) => {
    const newTemplates = [...(config.generator.templates || [])]
    newTemplates[index] = template
    const newConfig = {
      ...config,
      generator: {
        ...config.generator,
        templates: newTemplates,
      },
    }
    setConfig(newConfig)
    syncToYaml(newConfig)
  }

  // 删除模板
  const handleDeleteTemplate = (index) => {
    const newTemplates = [...(config.generator.templates || [])]
    newTemplates.splice(index, 1)
    const newConfig = {
      ...config,
      generator: {
        ...config.generator,
        templates: newTemplates,
      },
    }
    setConfig(newConfig)
    syncToYaml(newConfig)
  }

  // 如果只显示基础参数
  if (showOnlyBaseParams) {
    return (
      <div style={{ padding: '0' }}>
        <Form form={baseForm} layout="vertical" onValuesChange={handleBaseChange}>
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item name="time_interval" label="时间间隔（秒）" style={{ marginBottom: 8 }}>
                <InputNumber
                  style={{ width: '100%' }}
                  min={0.1}
                  step={0.1}
                  precision={1}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="history_points" label="历史数据点数" style={{ marginBottom: 8 }}>
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="future_points" label="未来数据点数" style={{ marginBottom: 8 }}>
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="start_time" label="起始时间" style={{ marginBottom: 8 }}>
                <DatePicker
                  showTime
                  format="YYYY-MM-DD HH:mm:ss"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </div>
    )
  }

  // 如果只显示模板
  if (showOnlyTemplates) {
    if (!config && yamlConfig) {
      return (
        <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
          正在解析YAML配置...
        </div>
      )
    }
    if (!config) {
      return (
        <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
          暂无配置内容，请先输入YAML配置
        </div>
      )
    }

    const handleDragStart = (index) => {
      setDraggedIndex(index)
    }

    const handleDragOver = (e, index) => {
      e.preventDefault()
      setDragOverIndex(index)
    }

    const handleDrop = (e, dropIndex) => {
      e.preventDefault()
      setDragOverIndex(null)
      
      try {
        const data = JSON.parse(e.dataTransfer.getData('application/json'))
        
        if (data.type === 'template-library') {
          // 从模板库拖拽：插入新模板
          const newTemplate = createTemplateByType(data.templateType)
          if (newTemplate) {
            const newTemplates = [...(config.generator.templates || [])]
            newTemplates.splice(dropIndex, 0, newTemplate)
            const newConfig = {
              ...config,
              generator: {
                ...config.generator,
                templates: newTemplates,
              },
            }
            setConfig(newConfig)
            syncToYaml(newConfig)
          }
        } else if (data.type === 'template-item') {
          // 拖拽排序：移动模板位置
          const dragIndex = data.index
          if (dragIndex !== dropIndex && dragIndex !== null) {
            const newTemplates = [...(config.generator.templates || [])]
            const [removed] = newTemplates.splice(dragIndex, 1)
            // 如果拖拽到后面，需要调整索引
            const insertIndex = dragIndex < dropIndex ? dropIndex - 1 : dropIndex
            newTemplates.splice(insertIndex, 0, removed)
            const newConfig = {
              ...config,
              generator: {
                ...config.generator,
                templates: newTemplates,
              },
            }
            setConfig(newConfig)
            syncToYaml(newConfig)
          }
        }
      } catch (error) {
        console.error('拖拽处理失败:', error)
      } finally {
        setDraggedIndex(null)
      }
    }

    const handleDragEnd = () => {
      setDraggedIndex(null)
      setDragOverIndex(null)
    }

    const createTemplateByType = (templateType) => {
      const timestamp = Date.now()
      // 只支持ExpressionTemplate
      if (templateType === 'ExpressionTemplate' || !templateType) {
        return {
          type: 'ExpressionTemplate',
          name: `template_${timestamp}`,
          config: {
            output_name: `F.template_${timestamp}`,
            calculation: {
              expression: '50 + 100 * sin(2 * pi * t / 86400)',
            },
            noise_level: 0.05,
          },
        }
      }
      // 默认返回ExpressionTemplate
      return {
        type: 'ExpressionTemplate',
        name: `template_${timestamp}`,
        config: {
          output_name: `F.template_${timestamp}`,
          calculation: {
            expression: '50 + 100 * sin(2 * pi * t / 86400)',
          },
          noise_level: 0.05,
        },
      }
    }

    return (
      <Row gutter={16} style={{ height: '100%', width: '100%', margin: 0 }}>
        {/* 左侧：模板列表 */}
        <Col flex="70%" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
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
            参数列表
          </div>
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '8px',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              backgroundColor: '#fff',
            }}
            onDragOver={(e) => {
              e.preventDefault()
              // 检查拖拽类型
              if (e.dataTransfer.types.includes('application/json')) {
                e.dataTransfer.dropEffect = 'copy'
              } else {
                e.dataTransfer.dropEffect = 'move'
              }
            }}
            onDrop={(e) => {
              e.preventDefault()
              e.stopPropagation()
              try {
                const data = JSON.parse(e.dataTransfer.getData('application/json'))
                if (data.type === 'template-library') {
                  // 拖拽到列表末尾
                  const newTemplate = createTemplateByType(data.templateType)
                  if (newTemplate) {
                    const newTemplates = [...(config.generator.templates || []), newTemplate]
                    const newConfig = {
                      ...config,
                      generator: {
                        ...config.generator,
                        templates: newTemplates,
                      },
                    }
                    setConfig(newConfig)
                    syncToYaml(newConfig)
                  }
                }
              } catch (error) {
                console.error('拖拽处理失败:', error)
              }
            }}
          >
            {(config.generator.templates || []).map((template, index) => (
              <div
                key={index}
                style={{
                  position: 'relative',
                }}
                onDragOver={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  // 检查拖拽类型（在onDragOver中无法使用getData，但可以检查types）
                  if (e.dataTransfer.types.includes('application/json')) {
                    e.dataTransfer.dropEffect = 'copy'
                  } else {
                    e.dataTransfer.dropEffect = 'move'
                  }
                  handleDragOver(e, index)
                }}
                onDrop={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleDrop(e, index)
                }}
              >
                {dragOverIndex === index && (
                  <div
                    style={{
                      position: 'absolute',
                      top: -4,
                      left: 0,
                      right: 0,
                      height: 2,
                      backgroundColor: '#1890ff',
                      zIndex: 10,
                    }}
                  />
                )}
                <TemplateCard
                  template={template}
                  index={index}
                  onUpdate={handleUpdateTemplate}
                  onDelete={handleDeleteTemplate}
                  availableOutputs={getAvailableOutputs()}
                  onDragStart={handleDragStart}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  isDragging={draggedIndex === index}
                  columnDescriptions={config.template?.column_descriptions || {}}
                />
              </div>
            ))}

            {(!config.generator.templates || config.generator.templates.length === 0) && (
              <Card>
                <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                  拖拽右侧模板到此处添加，或点击下方按钮添加
                </div>
              </Card>
            )}

            <div
              onDragOver={(e) => {
                e.preventDefault()
                e.stopPropagation()
                // 检查拖拽类型（在onDragOver中无法使用getData，但可以检查types）
                if (e.dataTransfer.types.includes('application/json')) {
                  e.dataTransfer.dropEffect = 'copy'
                } else {
                  e.dataTransfer.dropEffect = 'move'
                }
                const endIndex = (config.generator.templates || []).length
                setDragOverIndex(endIndex)
              }}
              onDrop={(e) => {
                e.preventDefault()
                e.stopPropagation()
                handleDrop(e, (config.generator.templates || []).length)
              }}
              style={{
                minHeight: 20,
                marginTop: 8,
                border: dragOverIndex === (config.generator.templates || []).length ? '2px dashed #1890ff' : '2px dashed transparent',
                borderRadius: 4,
                padding: 8,
                textAlign: 'center',
                color: '#999',
                fontSize: '12px',
              }}
            >
              拖拽到此处插入
            </div>
          </div>
        </Col>

        {/* 右侧：模板库 */}
        <Col flex="30%" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0, borderLeft: '1px solid #d9d9d9', paddingLeft: '16px' }}>
          <div
            style={{
              flex: 1,
              overflow: 'hidden',
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}
          >
            <TemplateLibrary />
          </div>
        </Col>
      </Row>
    )
  }

  // 完整显示（默认）
  return (
    <div style={{ padding: '20px' }}>
      {/* 基础参数配置 */}
      <Card title="基础参数" style={{ marginBottom: 20 }}>
        <Form form={baseForm} layout="vertical" onValuesChange={handleBaseChange}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Form.Item name="time_interval" label="时间间隔（秒）">
              <InputNumber
                style={{ width: '100%' }}
                min={0.1}
                step={0.1}
                precision={1}
              />
            </Form.Item>
            <Form.Item name="history_points" label="历史数据点数">
              <InputNumber style={{ width: '100%' }} min={1} />
            </Form.Item>
            <Form.Item name="future_points" label="未来数据点数">
              <InputNumber style={{ width: '100%' }} min={1} />
            </Form.Item>
            <Form.Item name="start_time" label="起始时间">
              <DatePicker
                showTime
                format="YYYY-MM-DD HH:mm:ss"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Space>
        </Form>
      </Card>

      <Divider />

      {/* 模板列表 */}
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAddTemplate}
        >
          添加模板
        </Button>
      </div>

      {(config.generator.templates || []).map((template, index) => (
        <TemplateCard
          key={index}
          template={template}
          index={index}
          onUpdate={handleUpdateTemplate}
          onDelete={handleDeleteTemplate}
          availableOutputs={getAvailableOutputs()}
        />
      ))}

      {(!config.generator.templates || config.generator.templates.length === 0) && (
        <Card>
          <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
            暂无模板，点击"添加模板"按钮添加
          </div>
        </Card>
      )}
    </div>
  )
}

export default VisualConfigEditor

