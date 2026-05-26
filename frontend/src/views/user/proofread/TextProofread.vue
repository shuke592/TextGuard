<template>
  <div class="text-proofread-page">
    <!-- 输入区域 -->
    <div v-if="!showResult" class="input-section">
      <el-card class="input-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">文本在线校对</span>
            <el-tag type="info" size="small">粘贴或输入文本，AI 智能审校</el-tag>
          </div>
        </template>

        <!-- 文本输入 -->
        <div class="editor-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="14"
            placeholder="请在此粘贴或输入需要校对的文本内容..."
            resize="vertical"
            maxlength="100000"
            show-word-limit
          />
        </div>

        <!-- 校对设置 -->
        <div class="proofread-settings">
          <div class="setting-row">
            <span class="setting-label">校对类型：</span>
            <el-checkbox-group v-model="checkTypes" class="setting-value">
              <el-checkbox value="typo">错别字</el-checkbox>
              <el-checkbox value="grammar">语法错误</el-checkbox>
              <el-checkbox value="punctuation">标点符号</el-checkbox>
              <el-checkbox value="style">表达优化</el-checkbox>
              <el-checkbox value="sensitive">敏感词</el-checkbox>
              <el-checkbox value="logic">逻辑问题</el-checkbox>
            </el-checkbox-group>
          </div>
          <div class="setting-row">
            <span class="setting-label">领域选择：</span>
            <el-radio-group v-model="domain" class="setting-value">
              <el-radio value="general">通用</el-radio>
              <el-radio value="official">公文</el-radio>
              <el-radio value="legal">法律</el-radio>
              <el-radio value="power">电力</el-radio>
              <el-radio value="new_energy">新能源</el-radio>
              <el-radio value="meter">电能表</el-radio>
            </el-radio-group>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-bar">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!inputText.trim()"
            @click="handleProofread"
          >
            <el-icon><Edit /></el-icon>
            {{ loading ? '校对中...' : '开始校对' }}
          </el-button>
          <el-button size="large" @click="inputText = ''">清空</el-button>
          <span class="text-count">{{ inputText.length }} 字</span>
        </div>
      </el-card>
    </div>

    <!-- 结果区域 -->
    <div v-else class="result-section">
      <!-- 顶部操作栏 -->
      <div class="result-toolbar">
        <el-button @click="goBack">
          <el-icon><Back /></el-icon>返回编辑
        </el-button>
        <div class="toolbar-info">
          <el-tag type="success">共发现 {{ issues.length }} 个问题</el-tag>
          <el-tag type="info">领域：{{ domainLabel }}</el-tag>
        </div>
        <div class="toolbar-actions">
          <el-button type="warning" @click="handleAcceptAll" :disabled="issues.length === 0">
            一键修改全部
          </el-button>
          <el-button @click="handleCopy">复制结果</el-button>
          <el-button type="primary" @click="handleExport">导出</el-button>
        </div>
      </div>

      <!-- 双栏对照 -->
      <div class="result-columns">
        <!-- 左栏：原文展示 -->
        <el-card class="column-card original-column">
          <template #header>
            <div class="column-header">
              <span class="column-title">
                <el-icon><Tickets /></el-icon>
                原文对照
              </span>
              <span class="text-count">{{ currentText.length }} 字</span>
            </div>
          </template>
          <div class="original-text" v-html="highlightedText"></div>
        </el-card>

        <!-- 右栏：问题列表 -->
        <el-card class="column-card issues-column">
          <template #header>
            <div class="issues-header">
              <span class="issues-title">
                <el-icon><Document /></el-icon>
                问题列表
                <el-tag type="info" effect="plain" size="small" round>{{ filteredIssues.length }}</el-tag>
              </span>
              <el-select
                v-model="filterType"
                placeholder="全部类型"
                clearable
                size="default"
                class="filter-select"
              >
                <template #prefix>
                  <el-icon><Filter /></el-icon>
                </template>
                <el-option label="全部类型" value="">
                  <el-icon style="vertical-align:middle;margin-right:6px;"><Menu /></el-icon>全部类型
                </el-option>
                <el-option label="错别字" value="typo">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#f56c6c;"><EditPen /></el-icon>错别字
                </el-option>
                <el-option label="语法错误" value="grammar">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#e6a23c;"><Reading /></el-icon>语法错误
                </el-option>
                <el-option label="标点符号" value="punctuation">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#909399;"><Operation /></el-icon>标点符号
                </el-option>
                <el-option label="表达优化" value="style">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#409eff;"><MagicStick /></el-icon>表达优化
                </el-option>
                <el-option label="敏感词" value="sensitive">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#f56c6c;"><Warning /></el-icon>敏感词
                </el-option>
                <el-option label="逻辑问题" value="logic">
                  <el-icon style="vertical-align:middle;margin-right:6px;color:#67c23a;"><Connection /></el-icon>逻辑问题
                </el-option>
              </el-select>
            </div>
          </template>
          <div class="issues-list">
            <div
              v-for="(issue, index) in filteredIssues"
              :key="index"
              class="issue-item"
              :class="{
                'is-accepted': issue._accepted,
                'is-ignored': issue._ignored,
                'is-active': activeIssueIndex === getGlobalIndex(issue),
              }"
              @mouseenter="activeIssueIndex = getGlobalIndex(issue)"
              @mouseleave="activeIssueIndex = -1"
            >
              <div class="issue-header">
                <span class="issue-number">#{{ getGlobalIndex(issue) + 1 }}</span>
                <el-tag :type="severityColor(issue.severity)" size="small" effect="dark">
                  {{ typeLabel(issue.type) }}
                </el-tag>
                <el-tag :type="severityTagType(issue.severity)" size="small" effect="plain">
                  {{ severityLabel(issue.severity) }}
                </el-tag>
              </div>
              <div class="issue-body">
                <div class="issue-diff">
                  <span class="text text-del" :title="issue.original">{{ issue.original }}</span>
                  <el-icon class="arrow-icon"><Right /></el-icon>
                  <span class="text text-add" :title="issue.suggestion">{{ issue.suggestion }}</span>
                </div>
                <div v-if="issue.explanation" class="issue-explanation">
                  <el-icon><InfoFilled /></el-icon>
                  <span>{{ issue.explanation }}</span>
                </div>
              </div>
              <div class="issue-actions" v-if="!issue._accepted && !issue._ignored">
                <el-button type="primary" size="small" @click="acceptIssue(index)">
                  <el-icon><Check /></el-icon>接受修改
                </el-button>
                <el-button size="small" @click="ignoreIssue(index)">
                  <el-icon><Close /></el-icon>忽略
                </el-button>
              </div>
              <div class="issue-status" v-else>
                <el-tag v-if="issue._accepted" type="success" size="small">已接受</el-tag>
                <el-tag v-if="issue._ignored" type="info" size="small">已忽略</el-tag>
                <el-button text size="small" @click="undoIssue(index)">撤销</el-button>
              </div>
            </div>
            <el-empty v-if="filteredIssues.length === 0" description="没有发现问题" />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { textProofreadApi, type ProofreadIssue } from '@/api/proofread'

interface IssueWithStatus extends ProofreadIssue {
  _accepted?: boolean
  _ignored?: boolean
}

// 状态
const inputText = ref('')
const loading = ref(false)
const showResult = ref(false)
const issues = ref<IssueWithStatus[]>([])
const currentText = ref('')
const filterType = ref('')
const activeIssueIndex = ref(-1)

// 设置
const checkTypes = ref<string[]>(['typo', 'grammar', 'punctuation', 'style'])
const domain = ref('general')

// 领域标签
const domainLabel = computed(() => {
  const map: Record<string, string> = {
    general: '通用', official: '公文', legal: '法律',
    power: '电力', new_energy: '新能源', meter: '电能表',
  }
  return map[domain.value] || '通用'
})

// 筛选后的问题列表
const filteredIssues = computed(() => {
  if (!filterType.value) return issues.value
  return issues.value.filter(i => i.type === filterType.value)
})

// 转义 HTML，避免原文中含有 < > 等字符破坏 DOM
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// 获取问题在全局列表中的索引（用于联动高亮）
function getGlobalIndex(issue: IssueWithStatus): number {
  return issues.value.indexOf(issue)
}

// 高亮原文（支持鼠标悬停联动）
const highlightedText = computed(() => {
  let text = escapeHtml(currentText.value)
  // 按原文片段进行高亮标记
  const activeIssues = issues.value.filter(i => !i._accepted && !i._ignored)
  for (const issue of activeIssues) {
    if (!issue.original) continue
    const globalIdx = issues.value.indexOf(issue)
    const escaped = escapeHtml(issue.original)
    if (!text.includes(escaped)) continue
    const isHover = activeIssueIndex.value === globalIdx
    const color = isHover ? '#fef3c7' : severityHighlight(issue.severity)
    const border = isHover ? 'box-shadow:0 0 0 2px #f59e0b;font-weight:600;' : ''
    const mark = `<mark data-issue-idx="${globalIdx}" style="background:${color};padding:2px 3px;border-radius:3px;cursor:pointer;transition:all .2s;${border}" title="[${typeLabel(issue.type)}] ${escapeHtml(issue.suggestion)}">${escaped}</mark>`
    text = text.replace(escaped, mark)
  }
  return text.replace(/\n/g, '<br/>')
})

function severityHighlight(severity: string): string {
  switch (severity) {
    case 'error': return '#fee2e2'  // 柔和红
    case 'warning': return '#fef3c7' // 柔和琥珀
    default: return '#dbeafe'        // 柔和蓝
  }
}

function severityColor(severity: string): 'danger' | 'warning' | 'info' | 'success' | 'primary' {
  switch (severity) {
    case 'error': return 'danger'
    case 'warning': return 'warning'
    default: return 'info'
  }
}

function severityTagType(severity: string): 'danger' | 'warning' | 'info' | 'success' | 'primary' {
  return severityColor(severity)
}

function severityLabel(severity: string): string {
  switch (severity) {
    case 'error': return '错误'
    case 'warning': return '警告'
    default: return '建议'
  }
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    typo: '错别字', grammar: '语法', punctuation: '标点',
    style: '表达', sensitive: '敏感词', logic: '逻辑',
  }
  return map[type] || type
}

// 开始校对
async function handleProofread() {
  if (!inputText.value.trim()) return
  loading.value = true
  try {
    const res = await textProofreadApi({
      text: inputText.value,
      check_types: checkTypes.value.length > 0 ? checkTypes.value : undefined,
      domain: domain.value,
    })
    issues.value = res.issues.map(i => ({ ...i, _accepted: false, _ignored: false }))
    currentText.value = inputText.value
    showResult.value = true
    if (res.total_issues === 0) {
      ElMessage.success('太棒了！文本没有发现任何问题')
    } else {
      ElMessage.info(`共发现 ${res.total_issues} 个问题`)
    }
  } catch (e: any) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 接受单条修改
function acceptIssue(index: number) {
  const issue = filteredIssues.value[index]
  if (issue.original && issue.suggestion) {
    currentText.value = currentText.value.replace(issue.original, issue.suggestion)
  }
  issue._accepted = true
}

// 忽略
function ignoreIssue(index: number) {
  filteredIssues.value[index]._ignored = true
}

// 撤销
function undoIssue(index: number) {
  const issue = filteredIssues.value[index]
  if (issue._accepted && issue.original && issue.suggestion) {
    currentText.value = currentText.value.replace(issue.suggestion, issue.original)
  }
  issue._accepted = false
  issue._ignored = false
}

// 一键修改全部
async function handleAcceptAll() {
  try {
    await ElMessageBox.confirm(
      `确认接受全部 ${issues.value.filter(i => !i._accepted && !i._ignored).length} 条修改建议？`,
      '一键修改',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    for (const issue of issues.value) {
      if (!issue._accepted && !issue._ignored && issue.original && issue.suggestion) {
        currentText.value = currentText.value.replace(issue.original, issue.suggestion)
        issue._accepted = true
      }
    }
    ElMessage.success('已接受所有修改')
  } catch {
    // 取消
  }
}

// 复制结果
function handleCopy() {
  navigator.clipboard.writeText(currentText.value)
  ElMessage.success('已复制到剪贴板')
}

// 导出
function handleExport() {
  const blob = new Blob([currentText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `校对结果_${new Date().toLocaleDateString()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 返回编辑
function goBack() {
  showResult.value = false
}
</script>

<style scoped lang="scss">
.text-proofread-page {
  max-width: 1400px;
  margin: 0 auto;
}

.input-card {
  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;

    .card-title {
      font-size: 18px;
      font-weight: 600;
    }
  }
}

.editor-wrapper {
  margin-bottom: 16px;

  :deep(.el-textarea__inner) {
    font-size: 15px;
    line-height: 1.8;
    font-family: var(--font-family);
  }
}

.proofread-settings {
  padding: 16px;
  background: #fafafa;
  border-radius: var(--border-radius-md);
  margin-bottom: 16px;

  .setting-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .setting-label {
      width: 80px;
      font-weight: 500;
      color: var(--color-text);
      flex-shrink: 0;
    }
  }
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;

  .text-count {
    margin-left: auto;
    color: var(--color-text-secondary);
    font-size: 13px;
  }
}

// 结果区域
.result-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);

  .toolbar-info {
    display: flex;
    gap: 8px;
  }

  .toolbar-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
}

.result-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  height: calc(100vh - 220px);

  .column-card {
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;

    :deep(.el-card__body) {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }
  }
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .column-title {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text);
  }

  .text-count {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.original-text {
  font-size: 15px;
  line-height: 2;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-all;
}

.issues-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .issues-title {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text);
  }
  .filter-select {
    width: 180px;
    :deep(.el-input__wrapper) {
      padding-left: 8px;
      border-radius: 8px;
    }
    :deep(.el-input__prefix) {
      color: var(--color-primary);
    }
  }
}

.issues-list {
  .issue-item {
    padding: 14px 14px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    margin-bottom: 12px;
    background: #ffffff;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);

    &:hover {
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
      border-color: #c7d2fe;
      transform: translateY(-1px);
    }

    &.is-active {
      border-color: #fbbf24;
      box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.12), 0 4px 12px rgba(251, 191, 36, 0.15);
      background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
    }

    &.is-accepted {
      opacity: 0.65;
      background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
      border-color: #bbf7d0;
    }

    &.is-ignored {
      opacity: 0.5;
      background: #fafafa;
      border-color: #e5e7eb;
    }
  }

  .issue-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;

    .issue-number {
      font-size: 11px;
      font-weight: 600;
      color: #6b7280;
      min-width: 28px;
      background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
      padding: 3px 7px;
      border-radius: 6px;
      letter-spacing: 0.02em;
    }
  }

  .issue-body {
    font-size: 14px;
    line-height: 1.6;

    // 原文 → 建议 单行高亮对比
    .issue-diff {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      padding: 12px 14px;
      background: linear-gradient(135deg, #fef2f2 0%, #fafafa 50%, #f0fdf4 100%);
      border-radius: 8px;
      margin-bottom: 10px;
      border: 1px solid #f3f4f6;

      .text {
        font-size: 15px;
        font-weight: 600;
        max-width: 100%;
        word-break: break-all;
        line-height: 1.5;
      }

      .text-del {
        color: #dc2626;
        text-decoration: line-through;
        text-decoration-thickness: 2px;
        text-decoration-color: #fca5a5;
      }

      .text-add {
        color: #059669;
      }

      .arrow-icon {
        font-size: 20px;
        color: #f59e0b;
        flex-shrink: 0;
        font-weight: bold;
      }
    }

    .issue-explanation {
      display: flex;
      align-items: flex-start;
      gap: 6px;
      color: #6b7280;
      font-size: 13px;
      padding: 6px 8px;
      background: #f9fafb;
      border-radius: 6px;
      border-left: 2px solid #e5e7eb;

      .el-icon {
        margin-top: 2px;
        color: #9ca3af;
        flex-shrink: 0;
      }
    }
  }

  .issue-actions, .issue-status {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 8px;

    .el-button .el-icon {
      margin-right: 4px;
    }
  }
}

/* ===== 移动端响应式 ===== */
@media (max-width: 768px) {
  .proofread-settings {
    padding: 12px;

    .setting-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;

      .setting-label {
        width: auto;
      }
    }
  }

  .result-columns {
    grid-template-columns: 1fr;
    height: auto;
  }

  .result-toolbar {
    flex-wrap: wrap;

    .toolbar-actions {
      margin-left: 0;
      width: 100%;
    }
  }
}
</style>
