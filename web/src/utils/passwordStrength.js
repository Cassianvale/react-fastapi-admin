/**
 * 密码强度检测工具
 * 基于后端密码策略配置进行前端验证
 */

// 密码策略配置（与后端config.py保持一致）
const PASSWORD_CONFIG = {
  MIN_LENGTH: 8,
  REQUIRE_UPPERCASE: true,
  REQUIRE_LOWERCASE: true,
  REQUIRE_DIGITS: true,
  REQUIRE_SPECIAL: true
}

/**
 * 检测密码强度
 * @param {string} password - 密码
 * @returns {Object} 强度检测结果
 */
export const checkPasswordStrength = (password) => {
  if (!password) {
    return {
      score: 0,
      level: 'weak',
      levelText: '弱',
      color: '#ff4d4f',
      suggestions: ['请输入密码'],
      passed: [],
      passedAll: false
    }
  }

  let score = 0
  const suggestions = []
  const passed = []
  let totalChecks = 0
  let passedChecks = 0

  // 计算总检查项数
  totalChecks++ // 长度检查
  if (PASSWORD_CONFIG.REQUIRE_UPPERCASE) totalChecks++
  if (PASSWORD_CONFIG.REQUIRE_LOWERCASE) totalChecks++
  if (PASSWORD_CONFIG.REQUIRE_DIGITS) totalChecks++
  if (PASSWORD_CONFIG.REQUIRE_SPECIAL) totalChecks++

  const pointsPerCheck = 100 / totalChecks

  // 长度检查
  if (password.length >= PASSWORD_CONFIG.MIN_LENGTH) {
    score += pointsPerCheck
    passedChecks++
    passed.push('length')
  } else {
    suggestions.push(`密码长度至少${PASSWORD_CONFIG.MIN_LENGTH}个字符`)
  }

  // 大写字母检查
  if (PASSWORD_CONFIG.REQUIRE_UPPERCASE) {
    if (/[A-Z]/.test(password)) {
      score += pointsPerCheck
      passedChecks++
      passed.push('uppercase')
    } else {
      suggestions.push('包含至少一个大写字母')
    }
  }

  // 小写字母检查
  if (PASSWORD_CONFIG.REQUIRE_LOWERCASE) {
    if (/[a-z]/.test(password)) {
      score += pointsPerCheck
      passedChecks++
      passed.push('lowercase')
    } else {
      suggestions.push('包含至少一个小写字母')
    }
  }

  // 数字检查
  if (PASSWORD_CONFIG.REQUIRE_DIGITS) {
    if (/\d/.test(password)) {
      score += pointsPerCheck
      passedChecks++
      passed.push('digits')
    } else {
      suggestions.push('包含至少一个数字')
    }
  }

  // 特殊字符检查
  if (PASSWORD_CONFIG.REQUIRE_SPECIAL) {
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      score += pointsPerCheck
      passedChecks++
      passed.push('special')
    } else {
      suggestions.push('包含至少一个特殊字符 (!@#$%^&*(),.?":{}|<>)')
    }
  }

  // 计算最终分数（最高100分）
  const finalScore = Math.min(100, Math.round(score))
  
  // 确定强度等级
  let level, levelText, color
  if (passedChecks === totalChecks) {
    level = 'strong'
    levelText = '强'
    color = '#52c41a'
  } else if (passedChecks >= Math.ceil(totalChecks * 0.7)) {
    level = 'medium'
    levelText = '中'
    color = '#faad14'
  } else {
    level = 'weak'
    levelText = '弱'
    color = '#ff4d4f'
  }

  return {
    score: finalScore,
    level,
    levelText,
    color,
    suggestions,
    passed,
    passedAll: passedChecks === totalChecks
  }
}

/**
 * 获取密码验证规则
 * @returns {Array} 验证规则数组
 */
export const getPasswordRules = () => {
  const rules = [
    { required: true, message: '请输入密码' },
    { min: PASSWORD_CONFIG.MIN_LENGTH, message: `密码长度不能少于${PASSWORD_CONFIG.MIN_LENGTH}个字符` }
  ]

  return rules
}

/**
 * 获取密码验证消息
 * @param {string} type - 验证类型
 * @returns {string} 验证消息
 */
export const getPasswordMessage = (type) => {
  const messages = {
    required: '请输入密码',
    minLength: `密码长度不能少于${PASSWORD_CONFIG.MIN_LENGTH}个字符`,
    uppercase: '必须包含至少一个大写字母',
    lowercase: '必须包含至少一个小写字母',
    digits: '必须包含至少一个数字',
    special: '必须包含至少一个特殊字符'
  }

  return messages[type] || '密码格式不正确'
}

/**
 * 生成密码强度提示
 * @returns {Array} 提示信息数组
 */
export const getPasswordHints = () => {
  const hints = []
  
  hints.push(`密码长度至少${PASSWORD_CONFIG.MIN_LENGTH}个字符`)
  
  if (PASSWORD_CONFIG.REQUIRE_UPPERCASE) {
    hints.push('包含至少一个大写字母')
  }
  
  if (PASSWORD_CONFIG.REQUIRE_LOWERCASE) {
    hints.push('包含至少一个小写字母')
  }
  
  if (PASSWORD_CONFIG.REQUIRE_DIGITS) {
    hints.push('包含至少一个数字')
  }
  
  if (PASSWORD_CONFIG.REQUIRE_SPECIAL) {
    hints.push('包含至少一个特殊字符（如!@#$%^&*）')
  }

  return hints
}