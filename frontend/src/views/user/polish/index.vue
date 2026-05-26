<template>
  <div class="polish-page">
    <div class="polish-layout">
      <!-- ===== 左侧：输入面板 ===== -->
      <div class="panel-left">
        <!-- 页面标题 -->
        <div class="page-header">
          <div class="header-title">
            <span class="title-icon">✨</span>
            <h2>AI 智能润色</h2>
          </div>
          <p class="header-desc">选择风格，一键获得专业级职场表达</p>
        </div>

        <!-- 敏感词警告（仅在检测到敏感词时显示） -->
        <transition name="fade-slide">
          <div v-if="showSensitiveWarning" class="sensitive-warning">
            <el-icon class="warning-icon"><WarningFilled /></el-icon>
            <span>内容将被发送至AI服务处理，请勿输入密码、身份证号等敏感信息</span>
          </div>
        </transition>

        <!-- 风格选择 -->
        <div class="style-section">
          <div class="section-title">
            <span>润色风格</span>
            <span class="style-selected-tag">{{ currentSelectedStyleName }}</span>
          </div>
          <div class="style-grid">
            <div
              v-for="item in styles"
              :key="item.key"
              class="style-card"
              :class="{ 'is-active': selectedStyle === item.key }"
              @click="selectedStyle = item.key"
            >
              <div class="card-icon">{{ styleIcons[item.key] || '✨' }}</div>
              <div class="card-content">
                <div class="card-name">{{ item.name }}</div>
                <div class="card-desc">{{ item.description }}</div>
              </div>
              <div v-if="selectedStyle === item.key" class="card-check">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 文本输入 -->
        <div class="input-section">
          <div class="section-title">
            <span>输入原文</span>
            <span class="char-count" :class="{ 'is-error': textTooShort || textTooLong }">
              {{ inputText.length }}/5000
            </span>
          </div>
          <div class="textarea-wrapper">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="8"
              placeholder="请在此粘贴或输入需要润色的文本内容（10-5000字）..."
              resize="none"
              maxlength="5000"
            />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-bar">
          <el-button
            class="btn-polish"
            type="primary"
            :loading="loading"
            :disabled="!canSubmit"
            @click="handlePolish"
          >
            <el-icon v-if="!loading"><MagicStick /></el-icon>
            {{ loading ? '正在润色...' : '一键润色' }}
          </el-button>
          <el-button class="btn-clear" @click="handleClear" :disabled="!inputText">
            <el-icon><Delete /></el-icon>清空
          </el-button>
        </div>
      </div>

      <!-- ===== 右侧：结果面板 ===== -->
      <div class="panel-right">
        <!-- 空状态 -->
        <div v-if="!hasResult && !loading" class="empty-state">
          <div class="empty-illustration">
            <span class="empty-icon">📝</span>
          </div>
          <h3>润色结果将在这里展示</h3>
          <p>输入文本并选择风格，点击「一键润色」即可生成三种不同程度的润色版本</p>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-animation">
            <div class="dot-pulse"></div>
          </div>
          <p>AI 正在为您润色，请稍候...</p>
          <span class="loading-tip">通常需要 10-30 秒</span>
        </div>

        <!-- 结果头部工具栏 -->
        <div v-if="hasResult && !loading" class="result-header">
          <div class="result-meta">
            <el-tag effect="dark" size="small" class="meta-tag">{{ currentStyleName }}</el-tag>
            <span class="meta-text">原文 {{ originalText.length }} 字</span>
          </div>
          <div class="result-actions">
            <el-button size="small" @click="handleRegenerate" :loading="regenerating">
              <el-icon><Refresh /></el-icon>重新生成
            </el-button>
          </div>
        </div>

        <!-- 三行润色结果 -->
        <div v-if="hasResult && !loading" class="result-list">
          <div
            v-for="(ver, idx) in versions"
            :key="idx"
            class="result-card"
            :class="'level-' + ver.level"
          >
            <!-- 卡片头部 -->
            <div class="card-head">
              <div class="card-badge" :class="'badge-' + ver.level">
                <span class="badge-num">{{ idx + 1 }}</span>
              </div>
              <span class="card-label">{{ ver.label }}</span>
              <el-tag
                :type="levelTagType(ver.level)"
                size="small"
                effect="plain"
                round
              >
                {{ levelDesc(ver.level) }}
              </el-tag>
              <el-button
                class="btn-copy"
                type="primary"
                size="small"
                text
                @click="handleCopy(ver.content)"
              >
                <el-icon><CopyDocument /></el-icon>复制
              </el-button>
            </div>
            <!-- 卡片内容（支持 Markdown） -->
            <div class="card-body markdown-body" v-html="renderMarkdown(ver.content)"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import {
  getPolishStylesApi,
  textPolishApi,
  type PolishStyle,
  type PolishVersion,
} from '@/api/polish'

// ---- Markdown 配置 ----
marked.setOptions({
  breaks: true,
  gfm: true,
})

// ---- 敏感关键词列表 ----
const SENSITIVE_KEYWORDS = [
  '密码', '身份证', '银行卡', '手机号', '验证码',
  '信用卡', '社保', '护照', '驾照', '账号密码',
  'password', 'token', 'secret', 'api_key', 'apikey',
]

// ---- 风格图标映射 ----
const styleIcons: Record<string, string> = {
  formal: '📋',
  friendly: '😊',
  plain: '💬',
  concise: '⚡',
  evidence: '📊',
  strategic: '🏔️',
  practical: '🎯',
  firm: '🤝',
  gentle: '🌸',
  action: '🚀',
}

// ---- 状态 ----
const styles = ref<PolishStyle[]>([])
const selectedStyle = ref('formal')
const inputText = ref('')
const loading = ref(false)
const regenerating = ref(false)
const versions = ref<PolishVersion[]>([])
const originalText = ref('')
const currentStyleName = ref('')
const showSensitiveWarning = ref(false)

// ---- 计算属性 ----
const textTooShort = computed(() => inputText.value.trim().length > 0 && inputText.value.trim().length < 10)
const textTooLong = computed(() => inputText.value.length > 5000)
const canSubmit = computed(() => {
  const len = inputText.value.trim().length
  return len >= 10 && len <= 5000
})
const hasResult = computed(() => versions.value.length > 0)
const currentSelectedStyleName = computed(() => {
  const found = styles.value.find(s => s.key === selectedStyle.value)
  return found ? found.name : '正式规范'
})

const currentSelectedStyleDesc = computed(() => {
  const found = styles.value.find(s => s.key === selectedStyle.value)
  return found ? found.description : '标准公文语体，结构完整、用词严谨、格式规范'
})

// ---- 敏感词检测 ----
watch(inputText, (val) => {
  const lower = val.toLowerCase()
  showSensitiveWarning.value = SENSITIVE_KEYWORDS.some(kw => lower.includes(kw.toLowerCase()))
})

// ---- 生命周期 ----
onMounted(async () => {
  try {
    const res = await getPolishStylesApi()
    styles.value = res.styles
  } catch {
    styles.value = [
      { key: 'formal', name: '正式规范', description: '标准公文语体，结构完整、用词严谨' },
      { key: 'friendly', name: '亲和自然', description: '像面对面聊天，去掉官腔，拉近距离' },
      { key: 'plain', name: '通俗易懂', description: '用大白话解释专业内容，降低理解门槛' },
      { key: 'concise', name: '极简干练', description: '只保留结论和关键信息，30秒看完' },
      { key: 'evidence', name: '有理有据', description: '每个观点都有数据或事实支撑' },
      { key: 'strategic', name: '高屋建瓴', description: '从战略视角出发，体现格局和高度' },
      { key: 'practical', name: '落地务实', description: '谁来做、怎么做、何时完成' },
      { key: 'firm', name: '温和坚定', description: '态度明确但不带攻击性' },
      { key: 'gentle', name: '委婉缓冲', description: '先肯定再提问题，降低抵触情绪' },
      { key: 'action', name: '推进行动', description: '结尾必带下一步动作和时间节点' },
    ]
  }
})

// ---- 方法 ----

/** Markdown 渲染 */
function renderMarkdown(content: string): string {
  if (!content) return ''
  return marked.parse(content) as string
}

/** 执行润色 */
async function handlePolish() {
  if (!canSubmit.value) return
  loading.value = true
  versions.value = []
  try {
    const res = await textPolishApi({
      text: inputText.value,
      style: selectedStyle.value,
    })
    versions.value = res.versions
    originalText.value = inputText.value
    currentStyleName.value = res.style_name
    ElMessage.success('润色完成')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

/** 清空输入 */
function handleClear() {
  inputText.value = ''
  versions.value = []
}

/** 重新生成 */
async function handleRegenerate() {
  regenerating.value = true
  loading.value = true
  versions.value = []
  try {
    const res = await textPolishApi({
      text: originalText.value,
      style: selectedStyle.value,
    })
    versions.value = res.versions
    currentStyleName.value = res.style_name
    ElMessage.success('已重新生成')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    regenerating.value = false
    loading.value = false
  }
}

/** 复制内容 */
async function handleCopy(content: string) {
  const html = compactRichHtml(renderMarkdown(content))
  const plainText = htmlToPlainText(html) || content

  try {
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': new Blob([html], { type: 'text/html' }),
          'text/plain': new Blob([plainText], { type: 'text/plain' }),
        }),
      ])
    } else {
      copyRichTextBySelection(html, plainText)
    }
    ElMessage.success('已复制带格式文本，可直接粘贴到飞书')
  } catch {
    try {
      copyRichTextBySelection(html, plainText)
      ElMessage.success('已复制带格式文本，可直接粘贴到飞书')
    } catch {
      await navigator.clipboard.writeText(plainText)
      ElMessage.success('已复制纯文本到剪贴板')
    }
  }
}

function htmlToPlainText(html: string): string {
  const container = document.createElement('div')
  container.innerHTML = html
  return compactPlainText(container.innerText)
}

function copyRichTextBySelection(html: string, plainText: string) {
  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.left = '-9999px'
  container.style.top = '0'
  container.style.whiteSpace = 'pre-wrap'
  container.innerHTML = html || plainText
  document.body.appendChild(container)

  const range = document.createRange()
  range.selectNodeContents(container)
  const selection = window.getSelection()
  selection?.removeAllRanges()
  selection?.addRange(range)

  const successful = document.execCommand('copy')
  selection?.removeAllRanges()
  document.body.removeChild(container)

  if (!successful) {
    throw new Error('复制失败')
  }
}

function compactRichHtml(html: string): string {
  const container = document.createElement('div')
  container.innerHTML = html

  container.querySelectorAll('p, h1, h2, h3, h4, h5, h6, ul, ol, blockquote').forEach((el) => {
    const node = el as HTMLElement
    node.style.marginTop = '0'
    node.style.marginBottom = node.tagName === 'LI' ? '0' : '6px'
    node.style.lineHeight = '1.55'
  })

  container.querySelectorAll('li').forEach((el) => {
    const node = el as HTMLElement
    node.style.marginTop = '0'
    node.style.marginBottom = '2px'
    node.style.lineHeight = '1.55'
  })

  container.querySelectorAll('br').forEach((br) => {
    const prev = br.previousSibling
    const next = br.nextSibling
    if ((!prev || !prev.textContent?.trim()) && (!next || !next.textContent?.trim())) {
      br.remove()
    }
  })

  container.querySelectorAll('p').forEach((p) => {
    if (!p.textContent?.trim()) {
      p.remove()
    }
  })

  return container.innerHTML
}

function compactPlainText(text: string): string {
  return text
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n[ \t]+/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n')
    .map(line => line.trimEnd())
    .join('\n')
    .trim()
}

/** 改动级别标签类型 */
function levelTagType(level: string): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (level) {
    case 'light': return 'success'
    case 'standard': return 'warning'
    case 'deep': return 'danger'
    default: return 'info'
  }
}

/** 改动级别描述 */
function levelDesc(level: string): string {
  switch (level) {
    case 'light': return '改动10~30%'
    case 'standard': return '改动40~60%'
    case 'deep': return '改动70~90%'
    default: return ''
  }
}
</script>

<style scoped lang="scss">
/* ===== 整体布局 ===== */
.polish-page {
  height: calc(100vh - 64px);
  overflow: hidden;
}

.polish-layout {
  display: flex;
  height: 100%;
  gap: 0;
}

/* ===== 左侧面板 ===== */
.panel-left {
  flex: 0 0 60%;
  max-width: 60%;
  min-width: 550px;
  padding: 24px;
  background: #ffffff;
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;

    .title-icon {
      font-size: 22px;
    }

    h2 {
      font-size: 20px;
      font-weight: 700;
      color: #1a1a2e;
      margin: 0;
      letter-spacing: -0.5px;
    }
  }

  .header-desc {
    margin: 6px 0 0;
    font-size: 13px;
    color: #9ca3af;
  }
}

/* 敏感词警告 */
.sensitive-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #fef3cd 0%, #fff9e6 100%);
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 12px;
  color: #92400e;

  .warning-icon {
    color: #f59e0b;
    font-size: 16px;
    flex-shrink: 0;
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 风格选择 */
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;

  .style-selected-tag {
    font-size: 12px;
    font-weight: 500;
    color: #0056b3;
    background: #eff6ff;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .char-count {
    font-weight: 400;
    color: #9ca3af;
    font-size: 12px;

    &.is-error {
      color: #ef4444;
      font-weight: 500;
    }
  }
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}

.style-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  background: #fff;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;

  .card-icon {
    font-size: 22px;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .card-content {
    flex: 1;
    min-width: 0;

    .card-name {
      font-size: 14px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 4px;
      line-height: 1.3;
    }

    .card-desc {
      font-size: 12px;
      color: #9ca3af;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  .card-check {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #0056b3;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
  }

  &:hover {
    border-color: #93c5fd;
    background: #f8faff;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 86, 179, 0.06);
  }

  &.is-active {
    border-color: #0056b3;
    background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
    box-shadow: 0 2px 10px rgba(0, 86, 179, 0.12);

    .card-name {
      color: #0056b3;
    }

    .card-desc {
      color: #6b7280;
    }
  }
}

/* 文本输入 */
.input-section {
  display: flex;
  flex-direction: column;
}

.textarea-wrapper {
  display: flex;
  flex-direction: column;

  :deep(.el-textarea) {
    display: flex;
    flex-direction: column;
  }

  :deep(.el-textarea__inner) {
    font-size: 14px;
    line-height: 1.75;
    border-radius: 10px;
    border: 1.5px solid #e5e7eb;
    padding: 14px 16px;
    resize: none;
    transition: border-color 0.2s;

    &:focus {
      border-color: #0056b3;
      box-shadow: 0 0 0 3px rgba(0, 86, 179, 0.06);
    }

    &::placeholder {
      color: #c4c9d4;
    }
  }
}

/* 操作按钮 */
.action-bar {
  display: flex;
  gap: 10px;

  .btn-polish {
    flex: 1;
    height: 42px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    background: linear-gradient(135deg, #0056b3 0%, #0077cc 100%);
    border: none;
    box-shadow: 0 4px 12px rgba(0, 86, 179, 0.25);

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(0, 86, 179, 0.35);
    }

    &:active:not(:disabled) {
      transform: translateY(0);
    }
  }

  .btn-clear {
    height: 42px;
    border-radius: 10px;
    border: 1.5px solid #e5e7eb;
    color: #6b7280;
  }
}

/* ===== 右侧面板 ===== */
.panel-right {
  flex: 1;
  padding: 24px;
  background: #f8f9fb;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;

  .empty-illustration {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;

    .empty-icon {
      font-size: 36px;
    }
  }

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #374151;
    margin: 0 0 8px;
  }

  p {
    font-size: 13px;
    color: #9ca3af;
    max-width: 280px;
    line-height: 1.6;
  }
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;

  p {
    margin-top: 20px;
    font-size: 15px;
    color: #374151;
    font-weight: 500;
  }

  .loading-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #9ca3af;
  }
}

.dot-pulse {
  position: relative;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #0056b3;
  animation: dot-pulse 1.5s infinite linear;

  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 0;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #0056b3;
  }

  &::before {
    left: -20px;
    animation: dot-pulse 1.5s infinite linear;
    animation-delay: -0.5s;
  }

  &::after {
    left: 20px;
    animation: dot-pulse 1.5s infinite linear;
    animation-delay: 0.5s;
  }
}

@keyframes dot-pulse {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* 结果头部 */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;

  .result-meta {
    display: flex;
    align-items: center;
    gap: 10px;

    .meta-tag {
      background: linear-gradient(135deg, #0056b3 0%, #0077cc 100%);
      border: none;
      border-radius: 6px;
    }

    .meta-text {
      font-size: 12px;
      color: #9ca3af;
    }
  }
}

/* 结果卡片列表 */
.result-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
}

.result-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    border-color: #e0e7ff;
    transform: translateY(-1px);
  }

  &.level-light {
    border-left: 3px solid #10b981;
  }

  &.level-standard {
    border-left: 3px solid #f59e0b;
  }

  &.level-deep {
    border-left: 3px solid #ef4444;
  }
}

.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f7f7f8;
  background: #fafbfc;

  .card-badge {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;

    .badge-num {
      font-size: 12px;
      font-weight: 700;
      color: #fff;
    }

    &.badge-light {
      background: linear-gradient(135deg, #10b981, #34d399);
    }

    &.badge-standard {
      background: linear-gradient(135deg, #f59e0b, #fbbf24);
    }

    &.badge-deep {
      background: linear-gradient(135deg, #ef4444, #f87171);
    }
  }

  .card-label {
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
  }

  .btn-copy {
    margin-left: auto;
    font-size: 12px;
  }
}

.card-body {
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
  max-height: calc((100vh - 240px) / 3 - 60px);
  overflow-y: auto;

  // Markdown 渲染样式
  :deep(p) {
    margin: 0 0 8px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(ul), :deep(ol) {
    margin: 4px 0 8px;
    padding-left: 20px;
  }

  :deep(li) {
    margin-bottom: 4px;
  }

  :deep(strong) {
    font-weight: 600;
    color: #111827;
  }

  :deep(code) {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    color: #e11d48;
  }

  :deep(blockquote) {
    margin: 8px 0;
    padding: 8px 12px;
    border-left: 3px solid #e5e7eb;
    background: #f9fafb;
    color: #6b7280;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin: 12px 0 6px;
    font-weight: 600;
    color: #111827;
  }

  :deep(h1) { font-size: 18px; }
  :deep(h2) { font-size: 16px; }
  :deep(h3) { font-size: 15px; }
  :deep(h4) { font-size: 14px; }
}

/* ===== 移动端响应式 ===== */
@media (max-width: 768px) {
  .polish-page {
    height: auto;
    overflow: auto;
  }

  .polish-layout {
    flex-direction: column;
    height: auto;
  }

  .panel-left {
    flex: none;
    max-width: 100%;
    min-width: 0;
    width: 100%;
    padding: 16px;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
    gap: 14px;
  }

  .page-header {
    .header-title h2 {
      font-size: 18px;
    }
    .header-desc {
      display: none;
    }
  }

  /* 移动端风格卡片：简化为紧凑 chip，隐藏说明 */
  .style-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }

  .style-card {
    padding: 8px 10px;
    gap: 6px;

    .card-icon {
      font-size: 18px;
    }

    .card-content {
      .card-name {
        font-size: 13px;
        margin-bottom: 0;
      }
      .card-desc {
        display: none;
      }
    }

    .card-check {
      width: 16px;
      height: 16px;
      top: 6px;
      right: 6px;
      font-size: 10px;
    }
  }

  .panel-right {
    padding: 16px;
    min-height: 300px;
  }

  .result-list {
    gap: 10px;
  }

  .card-body {
    max-height: none;
  }

  .action-bar {
    .btn-polish {
      height: 40px;
      font-size: 14px;
    }
    .btn-clear {
      height: 40px;
    }
  }
}
</style>
