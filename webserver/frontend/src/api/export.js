/**
 * 数据导出 API
 */

import axios from 'axios'

/**
 * 导出数据
 * @param {number} configId - 配置ID
 * @param {string} type - 导出类型：'history' 或 'full'
 * @param {string} configName - 配置名称（用于文件名）
 */
export const exportData = async (configId, type = 'full', configName = '') => {
  try {
    // 直接使用 axios，不使用拦截器，以便处理 blob 响应
    const response = await axios.get(`/api/export/${configId}`, {
      params: { type },
      responseType: 'blob',
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    const safeName = configName.replace(/[^a-zA-Z0-9_-]/g, '_')
    link.setAttribute('download', `${safeName}_${type}_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    return response.data
  } catch (error) {
    // 如果返回的是错误 JSON，尝试解析
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

