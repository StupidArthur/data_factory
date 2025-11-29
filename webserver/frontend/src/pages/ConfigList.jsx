/**
 * 配置列表页面
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Layout,
  Table,
  Button,
  Menu,
  Dropdown,
  Modal,
  message,
  Space,
  Input,
  Select,
  Upload,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UploadOutlined,
  MoreOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { getGroups, deleteGroup, createGroup } from '../api/groups'
import { getConfigs, deleteConfig, exportConfig, importConfig, checkConfigName, copyConfig } from '../api/configs'
import { exportData } from '../api/export'
import { importPresets } from '../api/presets'

const { Header, Content, Sider } = Layout
const { TextArea } = Input

function ConfigList() {
  const navigate = useNavigate()
  const [groups, setGroups] = useState([])
  const [configs, setConfigs] = useState([])
  const [selectedGroupId, setSelectedGroupId] = useState('all')
  const [loading, setLoading] = useState(false)
  const [createGroupModalVisible, setCreateGroupModalVisible] = useState(false)
  const [createGroupForm, setCreateGroupForm] = useState({
    name: '',
    description: '',
  })
  const [nameColumnWidth, setNameColumnWidth] = useState(300)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [importYamlContent, setImportYamlContent] = useState('')
  const [importConfigName, setImportConfigName] = useState('')
  const [copyModalVisible, setCopyModalVisible] = useState(false)
  const [copyConfigRecord, setCopyConfigRecord] = useState(null)
  const [copyConfigName, setCopyConfigName] = useState('')
  const [copyGroupId, setCopyGroupId] = useState(null)

  // 加载分组列表
  const loadGroups = useCallback(async () => {
    try {
      const result = await getGroups()
      if (result.success) {
        setGroups(result.data || [])
      }
    } catch (error) {
      message.error('加载分组列表失败: ' + error.message)
    }
  }, [])

  // 检查是否存在预设配置分组 - 使用 useMemo 优化
  const hasPresetGroup = useMemo(() => {
    return groups.some(group => group.name === '预设配置')
  }, [groups])

  // 加载配置列表 - 使用 useCallback 优化
  const loadConfigs = useCallback(async () => {
    setLoading(true)
    try {
      const groupId = selectedGroupId === 'all' ? null : parseInt(selectedGroupId)
      const result = await getConfigs(groupId)
      if (result.success) {
        setConfigs(result.data || [])
      }
    } catch (error) {
      message.error('加载配置列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [selectedGroupId])

  useEffect(() => {
    loadGroups()
  }, [])

  useEffect(() => {
    loadConfigs()
  }, [selectedGroupId])

  // 处理分组选择
  const handleGroupSelect = ({ key }) => {
    setSelectedGroupId(key)
  }

  // 创建分组
  const handleCreateGroup = useCallback(async () => {
    if (!createGroupForm.name) {
      message.warning('请输入分组名称')
      return
    }

    try {
      const result = await createGroup(createGroupForm)
      if (result.success) {
        message.success('创建分组成功')
        setCreateGroupModalVisible(false)
        setCreateGroupForm({ name: '', description: '' })
        // 延迟加载，避免阻塞UI
        setTimeout(() => {
          loadGroups()
        }, 100)
      }
    } catch (error) {
      message.error('创建分组失败: ' + error.message)
    }
  }, [createGroupForm, loadGroups])

  // 删除分组
  const handleDeleteGroup = (group) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除分组"${group.name}"吗？删除后，该分组下的所有配置将移动到"已删除"分组。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await deleteGroup(group.id)
          if (result.success) {
            message.success(result.message || '删除分组成功')
            loadGroups()
            if (String(group.id) === selectedGroupId) {
              setSelectedGroupId('all')
            }
            loadConfigs()
          }
        } catch (error) {
          message.error('删除分组失败: ' + error.message)
        }
      },
    })
  }

  // 导出数据 - 使用 useCallback 优化
  const handleExportData = useCallback(async (config) => {
    try {
      // 导出历史数据
      await exportData(config.id, 'history', config.name)
      // 等待一小段时间后导出完整数据
      setTimeout(async () => {
        await exportData(config.id, 'full', config.name)
        message.success('导出成功')
      }, 500)
    } catch (error) {
      message.error('导出失败: ' + (error.message || '未知错误'))
    }
  }, [])

  // 导出配置 - 使用 useCallback 优化
  const handleExportConfig = useCallback(async (config) => {
    try {
      await exportConfig(config.id, config.name)
      message.success('导出配置成功')
    } catch (error) {
      message.error('导出配置失败: ' + (error.message || '未知错误'))
    }
  }, [])

  // 打开拷贝配置对话框
  const handleOpenCopyModal = useCallback(async (record) => {
    setCopyConfigRecord(record)
    setCopyConfigName(record.name)
    setCopyGroupId(null)
    
    // 检查配置名称并获取不重复的名称
    try {
      const result = await checkConfigName(record.name)
      if (result.success && result.name) {
        setCopyConfigName(result.name)
      }
    } catch (error) {
      console.error('检查配置名称失败:', error)
    }
    
    setCopyModalVisible(true)
  }, [])

  // 拷贝配置
  const handleCopyConfig = useCallback(async () => {
    if (!copyConfigName || !copyConfigRecord) {
      message.warning('请输入配置名称')
      return
    }

    try {
      const result = await copyConfig(copyConfigRecord.id, {
        name: copyConfigName,
        group_id: copyGroupId,
        description: `拷贝自：${copyConfigRecord.name}`,
      })
      if (result.success) {
        const finalName = result.data?.name || copyConfigName
        if (result.message) {
          message.success(result.message)
        } else {
          message.success(`拷贝配置成功，配置名称：${finalName}`)
        }
        setCopyModalVisible(false)
        setCopyConfigRecord(null)
        setCopyConfigName('')
        setCopyGroupId(null)
        // 延迟加载，避免阻塞UI
        setTimeout(() => {
          loadConfigs()
        }, 100)
      }
    } catch (error) {
      message.error('拷贝配置失败: ' + (error.message || '未知错误'))
    }
  }, [copyConfigName, copyConfigRecord, copyGroupId, loadConfigs])

  // 处理文件上传
  const handleFileUpload = async (file) => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      const content = e.target.result
      setImportYamlContent(content)
      // 尝试从文件名提取配置名称
      const fileName = file.name.replace(/\.yaml$|\.yml$/i, '')
      
      // 检查配置名称并获取不重复的名称
      try {
        const result = await checkConfigName(fileName)
        if (result.success && result.name) {
          setImportConfigName(result.name)
        } else {
          setImportConfigName(fileName)
        }
      } catch (error) {
        // 如果检查失败，使用原始文件名
        console.error('检查配置名称失败:', error)
        setImportConfigName(fileName)
      }
      
      setImportModalVisible(true)
    }
    reader.readAsText(file)
    return false // 阻止自动上传
  }

  // 导入配置
  const handleImportConfig = useCallback(async () => {
    if (!importConfigName || !importYamlContent) {
      message.warning('请输入配置名称和YAML内容')
      return
    }

    try {
      const result = await importConfig({
        name: importConfigName,
        config_yaml: importYamlContent,
        group_id: selectedGroupId === 'all' ? null : parseInt(selectedGroupId),
        description: `导入的配置：${importConfigName}`,
      })
      if (result.success) {
        const finalName = result.data?.name || importConfigName
        if (result.message) {
          message.success(result.message)
        } else {
          message.success(`导入配置成功，配置名称：${finalName}`)
        }
        setImportModalVisible(false)
        setImportYamlContent('')
        setImportConfigName('')
        // 延迟加载，避免阻塞UI
        setTimeout(() => {
          loadConfigs()
        }, 100)
      }
    } catch (error) {
      message.error('导入配置失败: ' + (error.message || '未知错误'))
    }
  }, [importConfigName, importYamlContent, selectedGroupId, loadConfigs])

  // 删除配置 - 使用 useCallback 优化
  const handleDeleteConfig = useCallback((config) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除配置"${config.name}"吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await deleteConfig(config.id)
          if (result.success) {
            message.success('删除成功')
            // 延迟加载，避免阻塞UI
            setTimeout(() => {
              loadConfigs()
            }, 100)
          }
        } catch (error) {
          message.error('删除失败: ' + error.message)
        }
      },
    })
  }, [loadConfigs])

  // 当前页的数据 - 使用 useMemo 优化
  const paginatedConfigs = useMemo(() => {
    return configs.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  }, [configs, currentPage, pageSize])

  // 表格列定义 - 使用 useMemo 优化，避免每次渲染都重新创建
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      fixed: 'left',
    },
    {
      title: (
        <div style={{ position: 'relative', paddingRight: '8px' }}>
          <span>配置名称</span>
          <div
            style={{
              position: 'absolute',
              right: 0,
              top: 0,
              bottom: 0,
              width: '4px',
              cursor: 'col-resize',
              backgroundColor: 'transparent',
            }}
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              const startX = e.pageX
              const startWidth = nameColumnWidth
              
              const handleMouseMove = (e) => {
                const diff = e.pageX - startX
                const newWidth = Math.max(100, startWidth + diff)
                setNameColumnWidth(newWidth)
              }
              
              const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove)
                document.removeEventListener('mouseup', handleMouseUp)
                document.body.style.cursor = ''
                document.body.style.userSelect = ''
              }
              
              document.addEventListener('mousemove', handleMouseMove)
              document.addEventListener('mouseup', handleMouseUp)
              document.body.style.cursor = 'col-resize'
              document.body.style.userSelect = 'none'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#1890ff'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          />
        </div>
      ),
      dataIndex: 'name',
      key: 'name',
      width: nameColumnWidth,
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <span style={{ whiteSpace: 'nowrap' }}>{text}</span>
      ),
    },
    {
      title: '配置分组',
      dataIndex: 'group_name',
      key: 'group_name',
      width: 110,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '配置描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: true,
      },
      // 不设置固定宽度，让它自适应剩余空间
    },
    {
      title: '配置用户',
      dataIndex: 'user',
      key: 'user',
      width: 100,
      render: (text) => text || 'null',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/config_edit/${record.id}`)}
          >
            编辑
          </Button>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'export-data',
                  label: '导出数据',
                  icon: <DownloadOutlined />,
                  onClick: () => handleExportData(record),
                },
                {
                  key: 'export-config',
                  label: '导出配置',
                  icon: <DownloadOutlined />,
                  onClick: () => handleExportConfig(record),
                },
                {
                  key: 'copy',
                  label: '拷贝到分组',
                  icon: <CopyOutlined />,
                  onClick: () => handleOpenCopyModal(record),
                },
                {
                  type: 'divider',
                },
                {
                  key: 'delete',
                  label: '删除',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDeleteConfig(record),
                },
              ],
            }}
            trigger={['click']}
          >
            <Button size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ], [navigate, handleExportData, handleExportConfig, handleDeleteConfig, handleOpenCopyModal, nameColumnWidth, setNameColumnWidth])

  // 分组菜单项
  const groupMenuItems = groups.map((group) => ({
    key: String(group.id),
    label: (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{group.name}</span>
        <Dropdown
          menu={{
            items: [
              {
                key: 'delete',
                label: '删除分组',
                danger: true,
                onClick: () => handleDeleteGroup(group),
              },
            ],
          }}
          trigger={['click']}
        >
          <MoreOutlined
            style={{ cursor: 'pointer', opacity: 0.6 }}
            onClick={(e) => e.stopPropagation()}
          />
        </Dropdown>
      </div>
    ),
  }))

  return (
    <Layout className="main-container">
      <Header className="header">
        <h1>数据工厂 - 配置管理</h1>
        <span style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.6)', fontWeight: 400 }}>
          designed by @yuzechao
        </span>
      </Header>
      <Layout className="content-container">
        <Sider className="sidebar" width={250}>
          <div style={{ padding: '15px', borderBottom: '1px solid #ebeef5' }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                block
                onClick={() => setCreateGroupModalVisible(true)}
              >
                新建分组
              </Button>
              {!hasPresetGroup && (
                <Button
                  size="small"
                  block
                  onClick={async () => {
                    try {
                      const result = await importPresets('预设配置')
                      if (result.success) {
                        message.success(result.message || '导入成功')
                        loadGroups()
                        loadConfigs()
                      }
                    } catch (error) {
                      message.error('导入预设配置失败: ' + error.message)
                    }
                  }}
                >
                  导入预设配置
                </Button>
              )}
            </Space>
          </div>
          <Menu
            mode="inline"
            selectedKeys={[selectedGroupId]}
            items={[
              {
                key: 'all',
                label: '所有',
              },
              ...groupMenuItems,
            ]}
            onClick={handleGroupSelect}
          />
        </Sider>
        <Content className="main-content">
          <div className="view-container">
            <div className="view-header" style={{ flexShrink: 0 }}>
              <h2>配置列表</h2>
              <Space>
                <Upload
                  accept=".yaml,.yml"
                  showUploadList={false}
                  beforeUpload={handleFileUpload}
                >
                  <Button icon={<UploadOutlined />}>
                    导入配置
                  </Button>
                </Upload>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/config_edit')}
                >
                  新建配置
                </Button>
              </Space>
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 0, overflowX: 'auto', width: '100%' }}>
              <Table
                columns={columns}
                dataSource={paginatedConfigs}
                rowKey="id"
                loading={loading}
                pagination={false}
                scroll={{ x: 'max-content' }}
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ flexShrink: 0, paddingTop: 16, borderTop: '1px solid #ebeef5', display: 'flex', justifyContent: 'flex-end' }}>
              <Space>
                <span style={{ fontSize: '14px', color: '#666' }}>
                  共 {configs.length} 条
                </span>
                <Button
                  size="small"
                  disabled={loading || currentPage === 1}
                  onClick={() => {
                    if (currentPage > 1) {
                      setCurrentPage(currentPage - 1)
                    }
                  }}
                >
                  上一页
                </Button>
                <span style={{ fontSize: '14px', color: '#666' }}>
                  第 {currentPage} 页 / 共 {Math.ceil(configs.length / pageSize)} 页
                </span>
                <Button
                  size="small"
                  disabled={loading || currentPage >= Math.ceil(configs.length / pageSize)}
                  onClick={() => {
                    if (currentPage < Math.ceil(configs.length / pageSize)) {
                      setCurrentPage(currentPage + 1)
                    }
                  }}
                >
                  下一页
                </Button>
                <Select
                  size="small"
                  value={pageSize}
                  style={{ width: 100 }}
                  onChange={(value) => {
                    setPageSize(value)
                    setCurrentPage(1)
                  }}
                  options={[
                    { value: 10, label: '10 条/页' },
                    { value: 20, label: '20 条/页' },
                    { value: 50, label: '50 条/页' },
                    { value: 100, label: '100 条/页' },
                  ]}
                />
              </Space>
            </div>
          </div>
        </Content>
      </Layout>

      {/* 新建分组对话框 */}
      <Modal
        title="新建分组"
        open={createGroupModalVisible}
        onOk={handleCreateGroup}
        onCancel={() => {
          setCreateGroupModalVisible(false)
          setCreateGroupForm({ name: '', description: '' })
        }}
        okText="确定"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <div style={{ marginBottom: 8 }}>分组名称 <span style={{ color: 'red' }}>*</span></div>
            <Input
              value={createGroupForm.name}
              onChange={(e) =>
                setCreateGroupForm({ ...createGroupForm, name: e.target.value })
              }
              placeholder="请输入分组名称"
            />
          </div>
          <div>
            <div style={{ marginBottom: 8 }}>分组描述</div>
            <TextArea
              value={createGroupForm.description}
              onChange={(e) =>
                setCreateGroupForm({ ...createGroupForm, description: e.target.value })
              }
              placeholder="请输入分组描述"
              rows={3}
            />
          </div>
        </Space>
      </Modal>

      {/* 导入配置Modal */}
      <Modal
        title="导入配置"
        open={importModalVisible}
        onOk={handleImportConfig}
        onCancel={() => {
          setImportModalVisible(false)
          setImportYamlContent('')
          setImportConfigName('')
        }}
        okText="导入"
        cancelText="取消"
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>配置名称：</label>
            <Input
              value={importConfigName}
              onChange={(e) => setImportConfigName(e.target.value)}
              placeholder="请输入配置名称"
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>YAML配置内容：</label>
            <TextArea
              value={importYamlContent}
              onChange={(e) => setImportYamlContent(e.target.value)}
              rows={15}
              placeholder="YAML配置内容"
              style={{ fontFamily: 'monospace', fontSize: '12px' }}
            />
          </div>
        </Space>
      </Modal>

      {/* 拷贝配置Modal */}
      <Modal
        title="拷贝到分组"
        open={copyModalVisible}
        onOk={handleCopyConfig}
        onCancel={() => {
          setCopyModalVisible(false)
          setCopyConfigRecord(null)
          setCopyConfigName('')
          setCopyGroupId(null)
        }}
        okText="确定"
        cancelText="取消"
        width={500}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>配置名称：</label>
            <Input
              value={copyConfigName}
              onChange={(e) => setCopyConfigName(e.target.value)}
              placeholder="请输入配置名称"
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>目标分组：</label>
            <Select
              value={copyGroupId}
              onChange={(value) => setCopyGroupId(value)}
              placeholder="选择分组（可选）"
              allowClear
              style={{ width: '100%' }}
            >
              {groups.map((group) => (
                <Select.Option key={group.id} value={group.id}>
                  {group.name}
                </Select.Option>
              ))}
            </Select>
          </div>
        </Space>
      </Modal>
    </Layout>
  )
}

export default ConfigList

