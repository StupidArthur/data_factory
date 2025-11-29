/**
 * 分组管理 API
 */

import api from './index'

/**
 * 获取分组列表
 */
export const getGroups = () => {
  return api.get('/groups')
}

/**
 * 获取单个分组
 */
export const getGroup = (id) => {
  return api.get(`/groups/${id}`)
}

/**
 * 创建分组
 */
export const createGroup = (data) => {
  return api.post('/groups', data)
}

/**
 * 更新分组
 */
export const updateGroup = (id, data) => {
  return api.put(`/groups/${id}`, data)
}

/**
 * 删除分组
 */
export const deleteGroup = (id) => {
  return api.delete(`/groups/${id}`)
}

