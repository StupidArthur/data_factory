/**
 * 预设配置 API
 */

import api from './index'

/**
 * 获取预设文件列表
 */
export const getPresetFiles = () => {
  return api.get('/presets/list')
}

/**
 * 导入预设配置
 * @param {string} groupName - 分组名称（可选）
 */
export const importPresets = (groupName = '预设配置') => {
  return api.post('/presets/import', { group_name: groupName })
}

