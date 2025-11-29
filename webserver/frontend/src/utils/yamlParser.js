/**
 * YAML配置解析和生成工具
 */

import yaml from 'js-yaml'

/**
 * 解析YAML字符串为配置对象
 */
export function parseYamlConfig(yamlString) {
  try {
    if (!yamlString || typeof yamlString !== 'string') {
      return {
        success: false,
        error: 'YAML字符串为空或格式错误',
      }
    }
    
    const config = yaml.load(yamlString)
    console.log('yamlParser: 解析结果:', config)
    
    // 确保返回的对象有基本结构
    if (!config) {
      return {
        success: false,
        error: 'YAML解析结果为空',
      }
    }
    
    // 确保有generator字段
    if (!config.generator) {
      console.warn('yamlParser: 配置缺少generator字段，添加默认值')
      config.generator = {
        time_interval: 5.0,
        history_points: 10000,
        future_points: 120,
        start_time: '2024-01-01 00:00:00',
        templates: config.templates || [],
      }
    }
    
    // 确保templates是数组
    if (!Array.isArray(config.generator.templates)) {
      config.generator.templates = []
    }
    
    return {
      success: true,
      data: config,
    }
  } catch (error) {
    console.error('yamlParser: 解析异常:', error)
    return {
      success: false,
      error: error.message,
    }
  }
}

/**
 * 将配置对象转换为YAML字符串
 */
export function generateYamlConfig(config) {
  try {
    const yamlString = yaml.dump(config, {
      indent: 2,
      lineWidth: -1,
      quotingType: '"',
    })
    return {
      success: true,
      data: yamlString,
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
    }
  }
}

/**
 * 获取默认配置结构
 */
export function getDefaultConfig() {
  return {
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
}

