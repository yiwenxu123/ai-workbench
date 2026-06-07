/**
 * 错误消息映射 — 将技术错误转为友好提示
 */

interface ErrorInfo {
  title: string
  message: string
  action?: string
}

const ERROR_MAP: Record<string, ErrorInfo> = {
  // 网络错误
  'Network Error': {
    title: '网络连接失败',
    message: '无法连接到服务器，请检查网络是否正常',
    action: '检查网络后重试',
  },
  'Failed to fetch': {
    title: '网络连接失败',
    message: '请求未能送达服务器',
    action: '检查网络后重试',
  },

  // API 密钥
  'Invalid API key': {
    title: 'API 密钥无效',
    message: '当前配置的 API 密钥不正确或已过期',
    action: '重新配置',
  },
  'Unauthorized': {
    title: '认证失败',
    message: 'API 密钥验证未通过',
    action: '重新配置',
  },
  '401': {
    title: '认证失败',
    message: 'API 密钥验证未通过',
    action: '重新配置',
  },

  // 配额
  'Rate limit': {
    title: '请求过于频繁',
    message: '当前 API 调用频率超出限制',
    action: '稍后重试',
  },
  '429': {
    title: '请求过于频繁',
    message: '当前 API 调用频率超出限制',
    action: '稍后重试',
  },
  'Quota exceeded': {
    title: '配额已用完',
    message: '当前 API 额度已耗尽',
    action: '检查账户额度',
  },

  // 服务器
  '500': {
    title: '服务器错误',
    message: '服务端处理请求时出错',
    action: '稍后重试',
  },
  '502': {
    title: '服务暂时不可用',
    message: '上游服务未响应',
    action: '稍后重试',
  },
  '503': {
    title: '服务维护中',
    message: '当前服务正在维护',
    action: '稍后重试',
  },

  // 超时
  'timeout': {
    title: '请求超时',
    message: '服务器处理时间过长',
    action: '稍后重试',
  },

  // 内容审核
  'content_policy': {
    title: '内容不合规',
    message: '提示词包含被限制的内容',
    action: '修改提示词后重试',
  },
  'sensitive': {
    title: '内容不合规',
    message: '提示词包含敏感内容',
    action: '修改提示词后重试',
  },
}

/**
 * 根据错误消息返回友好的错误信息
 */
export function getErrorInfo(error: string | null | undefined): ErrorInfo {
  if (!error) {
    return { title: '未知错误', message: '发生了意外错误' }
  }

  const lower = error.toLowerCase()

  for (const [key, info] of Object.entries(ERROR_MAP)) {
    if (lower.includes(key.toLowerCase())) {
      return info
    }
  }

  // 检查 HTTP 状态码
  const statusMatch = error.match(/\b([45]\d{2})\b/)
  if (statusMatch && ERROR_MAP[statusMatch[1]]) {
    return ERROR_MAP[statusMatch[1]]
  }

  return { title: '生成失败', message: error }
}
