/**
 * 配置编辑页面
 */

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Layout,
  Form,
  Input,
  Button,
  Select,
  message,
  Space,
  Spin,
  Row,
  Col,
  Divider,
} from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { getGroups } from '../api/groups'
import { getConfig, createConfig, updateConfig } from '../api/configs'
import VisualConfigEditor from '../components/VisualConfigEditor'
import { getDefaultConfig } from '../utils/yamlParser'
import yaml from 'js-yaml'

const { Header, Content } = Layout
const { TextArea } = Input

// 默认配置模板（空模板列表）
const DEFAULT_CONFIG = yaml.dump(getDefaultConfig(), {
  allowUnicode: true,
  defaultFlowStyle: false,
})

function ConfigEdit() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [form] = Form.useForm()
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [yamlContent, setYamlContent] = useState('')
  const isEdit = !!id

  // 加载分组列表
  const loadGroups = async () => {
    try {
      const result = await getGroups()
      if (result.success) {
        setGroups(result.data || [])
      }
    } catch (error) {
      message.error('加载分组列表失败: ' + error.message)
    }
  }

  // 加载配置数据
  const loadConfig = async () => {
    setInitialLoading(true)
    if (!isEdit) {
      form.setFieldsValue({
        config_yaml: DEFAULT_CONFIG,
      })
      setYamlContent(DEFAULT_CONFIG)
      setInitialLoading(false)
      return
    }

    setLoading(true)
    try {
      const result = await getConfig(id)
      console.log('ConfigEdit: 加载配置结果:', result)
      if (result.success) {
        const config = result.data
        console.log('ConfigEdit: 配置数据:', config)
        console.log('ConfigEdit: YAML内容长度:', config.config_yaml?.length || 0)
        
        form.setFieldsValue({
          name: config.name,
          description: config.description || '',
          config_yaml: config.config_yaml,
          group_id: config.group_id,
          user: config.user || '',
        })
        
        const yamlContent = config.config_yaml || ''
        console.log('ConfigEdit: 设置YAML内容，长度:', yamlContent.length)
        setYamlContent(yamlContent)
      } else {
        console.error('ConfigEdit: 加载配置失败:', result.error)
        message.error('加载配置失败: ' + (result.error || '未知错误'))
      }
    } catch (error) {
      console.error('ConfigEdit: 加载配置异常:', error)
      message.error('加载配置失败: ' + error.message)
      // 不自动跳转，让用户看到错误信息
    } finally {
      setLoading(false)
      setInitialLoading(false)
    }
  }

  useEffect(() => {
    loadGroups()
  }, [])

  useEffect(() => {
    loadConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  // 处理YAML内容变化（从图形化编辑器同步）
  const handleYamlChange = (newYaml) => {
    if (newYaml && newYaml !== yamlContent) {
      setYamlContent(newYaml)
      form.setFieldsValue({
        config_yaml: newYaml,
      })
    }
  }

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      // 确保使用最新的YAML内容
      values.config_yaml = yamlContent || values.config_yaml
      setLoading(true)

      if (isEdit) {
        const result = await updateConfig(id, values)
        if (result.success) {
          message.success('保存成功')
          navigate('/')
        }
      } else {
        const result = await createConfig(values)
        if (result.success) {
          message.success('保存成功')
          navigate('/')
        }
      }
    } catch (error) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error('保存失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout className="main-container">
      <Header className="header">
        <h1>数据工厂 - {isEdit ? '编辑配置' : '新建配置'}</h1>
        <span style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.6)', fontWeight: 400 }}>
          designed by @yuzechao
        </span>
      </Header>
      <Content className="main-content" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="view-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="view-header" style={{ flex: '0 0 auto' }}>
            <h2>{isEdit ? '编辑配置' : '新建配置'}</h2>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                返回列表
              </Button>
              <Button type="primary" loading={loading} onClick={handleSave}>
                保存配置
              </Button>
            </Space>
          </div>

          <Spin spinning={initialLoading} tip="加载中...">
            <Row gutter={16} style={{ height: 'calc(100vh - 200px)', flex: 1, display: 'flex' }}>
              {/* 左侧：基本信息和基础参数 */}
              <Col flex="30%" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
                {/* 基本信息 */}
                <Form
                  form={form}
                  layout="vertical"
                  style={{ flex: '0 0 auto', marginBottom: 8 }}
                >
                  <Row gutter={8}>
                    <Col span={8}>
                      <Form.Item
                        name="name"
                        label="配置名称"
                        rules={[{ required: true, message: '请输入配置名称' }]}
                        style={{ marginBottom: 8 }}
                      >
                        <Input placeholder="配置名称" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="group_id"
                        label="配置分组"
                        style={{ marginBottom: 8 }}
                      >
                        <Select placeholder="选择分组" allowClear>
                          {groups.map((group) => (
                            <Select.Option key={group.id} value={group.id}>
                              {group.name}
                            </Select.Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="user"
                        label="配置用户"
                        style={{ marginBottom: 8 }}
                      >
                        <Input placeholder="配置用户" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    name="description"
                    label="配置描述"
                    style={{ marginBottom: 8 }}
                  >
                    <TextArea
                      placeholder="请输入配置描述"
                      rows={2}
                    />
                  </Form.Item>

                  <Divider style={{ margin: '8px 0' }}>基础参数</Divider>

                  {/* 基础参数配置（每行两个） */}
                  <div style={{ marginBottom: 8 }}>
                    <VisualConfigEditor
                      yamlConfig={yamlContent}
                      onChange={handleYamlChange}
                      showOnlyBaseParams={true}
                    />
                  </div>
                </Form>

                <Divider style={{ margin: '8px 0' }}>YAML文本编辑器</Divider>

                {/* YAML编辑器 - 占据剩余空间 */}
                <div 
                  style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden', position: 'relative' }}
                  className="yaml-editor-container"
                >
                  <style>{`
                    .yaml-editor-container .ant-form-item {
                      height: 100% !important;
                      width: 100% !important;
                    }
                    .yaml-editor-container .ant-form-item-row {
                      height: 100% !important;
                      width: 100% !important;
                    }
                    .yaml-editor-container .ant-form-item-control {
                      height: 100% !important;
                      width: 100% !important;
                      display: flex;
                      flex-direction: column;
                    }
                    .yaml-editor-container .ant-form-item-control-input {
                      height: 100% !important;
                      width: 100% !important;
                      flex: 1;
                      display: flex;
                      flex-direction: column;
                    }
                    .yaml-editor-container .ant-form-item-control-input-content {
                      height: 100% !important;
                      width: 100% !important;
                      flex: 1;
                      display: flex;
                      flex-direction: column;
                    }
                    .yaml-editor-container .ant-form-item-control-input-content textarea {
                      height: 100% !important;
                      width: 100% !important;
                      flex: 1;
                    }
                  `}</style>
                  <Form.Item
                    name="config_yaml"
                    style={{ 
                      marginBottom: 0,
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      height: '100%',
                    }}
                  >
                    <TextArea
                      placeholder="YAML配置内容将根据右侧图形化编辑自动生成"
                      readOnly
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        height: '100%',
                        width: '100%',
                        resize: 'none',
                        backgroundColor: '#fafafa',
                        cursor: 'default',
                      }}
                      value={yamlContent}
                    />
                  </Form.Item>
                </div>
              </Col>

              {/* 右侧：模板配置 */}
              <Col flex="70%" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                <div style={{ 
                  marginBottom: 8, 
                  fontWeight: 600,
                  fontSize: '15px',
                  color: '#1890ff',
                  padding: '8px 12px',
                  backgroundColor: '#e6f7ff',
                  border: '1px solid #91d5ff',
                  borderRadius: '4px',
                }}>
                  模板配置
                </div>
                <div
                  style={{
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    flex: 1,
                    overflowY: 'auto',
                    overflowX: 'hidden',
                    backgroundColor: '#fafafa',
                    minHeight: 0,
                  }}
                >
                  <VisualConfigEditor
                    yamlConfig={yamlContent}
                    onChange={handleYamlChange}
                    showOnlyTemplates={true}
                  />
                </div>
              </Col>
            </Row>
          </Spin>
        </div>
      </Content>
    </Layout>
  )
}

export default ConfigEdit

