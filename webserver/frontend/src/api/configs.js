/**
 * 配置管理 API
 */

import api from './index'
import axios from 'axios'

/**
 * 获取配置列表
 * @param {number} groupId - 分组ID（可选）
 */
export const getConfigs = (groupId = null) => {
  const params = groupId ? { group_id: groupId } : {}
  return api.get('/configs', { params })
}

/**
 * 获取单个配置
 */
export const getConfig = (id) => {
  return api.get(`/configs/${id}`)
}

/**
 * 创建配置
 */
export const createConfig = (data) => {
  return api.post('/configs', data)
}

/**
 * 更新配置
 */
export const updateConfig = (id, data) => {
  return api.put(`/configs/${id}`, data)
}

/**
 * 删除配置
 */
export const deleteConfig = (id) => {
  return api.delete(`/configs/${id}`)
}

/**
 * 导出配置为YAML文件
 */
export const exportConfig = async (configId, configName) => {
  try {
    const response = await axios.get(`/api/configs/${configId}/export`, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    const safeName = configName.replace(/[^a-zA-Z0-9_-]/g, '_')
    link.setAttribute('download', `${safeName}.yaml`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    return response.data
  } catch (error) {
    if (error.response?.data instanceof Blob) {
      const text = await error.response.data.text()
      try {
        const errorData = JSON.parse(text)
        throw new Error(errorData.error || '导出失败')
      } catch {
        throw new Error('导出失败')
      }
    }
    throw error
  }
}

/**
 * 导入配置
 */
export const importConfig = (data) => {
  return api.post('/configs/import', data)
}

/**
 * 检查配置名称并返回不重复的名称
 */
export const checkConfigName = (name) => {
  return api.get('/configs/check-name', { params: { name } })
}

/**
 * 拷贝配置到新分组
 */
export const copyConfig = (configId, data) => {
  return api.post(`/configs/${configId}/copy`, data)
}

