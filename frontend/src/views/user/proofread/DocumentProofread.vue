<template>
  <div class="document-proofread-page">
    <!-- 步骤一：上传文件 -->
    <div v-if="step === 'upload'" class="upload-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span class="card-title">文档上传校对</span>
            <el-tag type="info" size="small">支持 .doc / .docx / .pdf / .txt 格式，最大 20MB</el-tag>
          </div>
        </template>

        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="() => ElMessage.warning('只能上传一个文件')"
          accept=".doc,.docx,.pdf,.txt"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="upload-tip">支持 .doc / .docx / .pdf / .txt 格式，单文件最大 20MB，PDF 最多 100 页</div>
          </template>
        </el-upload>

        <!-- 校对设置 -->
        <div class="proofread-settings" v-if="selectedFile">
          <div class="file-info">
            <el-icon><Document /></el-icon>
            <span>{{ selectedFile.name }}</span>
            <el-tag size="small">{{ formatSize(selectedFile.size) }}</el-tag>
          </div>
          <div class="setting-row">
            <span class="setting-label">校对类型：</span>
            <el-checkbox-group v-model="checkTypes">
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
            <el-radio-group v-model="domain">
              <el-radio value="general">通用</el-radio>
              <el-radio value="official">公文</el-radio>
              <el-radio value="legal">法律</el-radio>
              <el-radio value="power">电力</el-radio>
              <el-radio value="new_energy">新能源</el-radio>
              <el-radio value="meter">电能表</el-radio>
            </el-radio-group>
          </div>
          <el-button type="primary" size="large" :loading="uploading || proofreading" @click="handleStartProofread">
            <el-icon><Edit /></el-icon>
            {{ statusText }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 步骤二：校对进度 -->
    <div v-else-if="step === 'processing'" class="processing-section">
      <el-card>
        <div class="processing-content">
          <el-icon class="processing-icon" :size="48"><Loading /></el-icon>
          <h3>{{ statusText }}</h3>
          <p class="processing-info">{{ processingInfo }}</p>
          <el-progress :percentage="progress" :stroke-width="8" style="width: 400px; margin-top: 16px;" />
        </div>
      </el-card>
    </div>

    <!-- 步骤三：双栏对照结果 -->
    <div v-else-if="step === 'result'" class="result-section">
      <!-- 顶部操作栏 -->
      <div class="result-toolbar">
        <el-button @click="resetAll">
          <el-icon><Back /></el-icon>重新上传
        </el-button>
        <div class="toolbar-info">
          <el-tag><el-icon><Document /></el-icon>&nbsp;{{ resultFilename }}</el-tag>
          <el-tag type="success">共 {{ issues.length }} 个问题</el-tag>
          <el-tag type="info">{{ acceptedCount }} 已接受</el-tag>
          <el-tag type="warning">{{ pendingCount }} 待处理</el-tag>
        </div>
        <div class="toolbar-actions">
          <el-button type="warning" @click="handleAcceptAll" :disabled="pendingCount === 0">
            一键修改全部
          </el-button>
          <el-button type="primary" @click="handleExportText">
            <el-icon><Download /></el-icon>导出修订文本
          </el-button>
          <el-button
            v-if="correctedDownloadUrl"
            @click="downloadCorrected"
          >
            下载修订文档
          </el-button>
          <el-button @click="handleExportReport">导出问题报告</el-button>
        </div>
      </div>

      <!-- 双栏对照区域 -->
      <div class="result-columns">
        <!-- 左栏：原文（带高亮标注） -->
        <el-card class="column-card original-column">
          <template #header>
            <div class="column-header">
              <span>文档原文</span>
              <span class="text-count">{{ originalText.length }} 字</span>
            </div>
          </template>
          <div class="original-text" v-html="highlightedText"></div>
        </el-card>

        <!-- 右栏：问题列表（逐条审改） -->
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
                <el-tag :type="severityColor(issue.severity)" size="small">
                  {{ typeLabel(issue.type) }}
                </el-tag>
                <el-tag :type="severityColor(issue.severity)" size="small" effect="plain">
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
                <el-button type="primary" size="small" @click="acceptIssue(issue)">
                  <el-icon><Check /></el-icon>接受修改
                </el-button>
                <el-button size="small" @click="ignoreIssue(issue)">
                  <el-icon><Close /></el-icon>忽略
                </el-button>
              </div>
              <div class="issue-status" v-else>
                <el-tag v-if="issue._accepted" type="success" size="small">已接受</el-tag>
                <el-tag v-if="issue._ignored" type="info" size="small">已忽略</el-tag>
                <el-button text size="small" @click="undoIssue(issue)">撤销</el-button>
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
import {
  uploadDocumentApi,
  documentProofreadApi,
  type DocumentUploadResponse,
  type DocumentProofreadResponse,
} from '@/api/document'

interface IssueWithStatus {
  original: string
  type: string
  suggestion: string
  explanation: string
  severity: string
  chunk_index: number
  _accepted: boolean
  _ignored: boolean
}

// 步骤状态
const step = ref<'upload' | 'processing' | 'result'>('upload')
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const proofreading = ref(false)
const progress = ref(0)
const processingInfo = ref('')

// 设置
const checkTypes = ref<string[]>(['typo', 'grammar', 'punctuation', 'style'])
const domain = ref('general')

// 结果数据
const originalText = ref('')
const currentText = ref('')
const currentHtml = ref('')
const resultFilename = ref('')
const correctedDownloadUrl = ref('')
const issues = ref<IssueWithStatus[]>([])
const filterType = ref('')
const activeIssueIndex = ref(-1)

// 计算属性
const statusText = computed(() => {
  if (uploading.value) return '上传中...'
  if (proofreading.value) return 'AI 校对中...'
  return '开始校对'
})

const acceptedCount = computed(() => issues.value.filter(i => i._accepted).length)
const pendingCount = computed(() => issues.value.filter(i => !i._accepted && !i._ignored).length)

const filteredIssues = computed(() => {
  if (!filterType.value) return issues.value
  return issues.value.filter(i => i.type === filterType.value)
})

const highlightedText = computed(() => {
  // 优先使用格式化 HTML（保留 Word 排版），回退到纯文本
  let html = currentHtml.value
  if (!html) {
    html = escapeHtml(currentText.value).replace(/\n/g, '<br/>')
  }
  const activeIssues = issues.value.filter(i => !i._accepted && !i._ignored)
  for (const issue of activeIssues) {
    if (!issue.original) continue
    const globalIdx = issues.value.indexOf(issue)
    const isHover = activeIssueIndex.value === globalIdx
    const color = isHover ? '#fef3c7' : severityHighlight(issue.severity)
    const border = isHover ? 'box-shadow:0 0 0 2px #f59e0b;' : ''
    const markHtml = `<mark class="highlight-mark" style="background:${color};${border}padding:1px 3px;border-radius:2px;cursor:pointer;" title="[${typeLabel(issue.type)}] ${escapeHtml(issue.suggestion)}">${escapeHtml(issue.original)}</mark>`
    html = replaceTextInHtml(html, issue.original, markHtml)
  }
  return html
})

// HTML 工具函数：仅在文本节点中替换，跳过 HTML 标签
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function replaceTextInHtml(html: string, searchPlain: string, replacementHtml: string): string {
  const search = escapeHtml(searchPlain)
  let replaced = false
  return html.replace(/(<[^>]*>)|([^<]+)/g, (match: string, tag: string, text: string) => {
    if (tag || replaced) return match
    if (text && text.includes(search)) {
      replaced = true
      return text.replace(search, replacementHtml)
    }
    return match
  })
}

// 辅助函数
function getGlobalIndex(issue: IssueWithStatus): number {
  return issues.value.indexOf(issue)
}

function severityHighlight(severity: string): string {
  switch (severity) {
    case 'error': return '#fee2e2'  // 柔和红
    case 'warning': return '#fef3c7' // 柔和琥珀
    default: return '#dbeafe'        // 柔和蓝
  }
}

function severityColor(severity: string): 'danger' | 'warning' | 'info' {
  switch (severity) {
    case 'error': return 'danger'
    case 'warning': return 'warning'
    default: return 'info'
  }
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

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

// 开始校对
async function handleStartProofread() {
  if (!selectedFile.value) return

  try {
    // 步骤1: 上传文件
    step.value = 'processing'
    uploading.value = true
    progress.value = 20
    processingInfo.value = '正在上传文件并提取文本...'

    const uploadRes = await uploadDocumentApi(selectedFile.value)
    uploading.value = false
    progress.value = 40
    processingInfo.value = `文本提取完成，共 ${uploadRes.text_length} 字，正在调用 AI 校对...`

    // 保存提取的文本和格式化 HTML
    originalText.value = uploadRes.extracted_text
    currentText.value = uploadRes.extracted_text
    currentHtml.value = uploadRes.extracted_html || ''

    // 步骤2: 执行校对
    proofreading.value = true
    progress.value = 60

    const proofreadRes = await documentProofreadApi({
      file_id: uploadRes.file_id,
      check_types: checkTypes.value.length > 0 ? checkTypes.value : undefined,
      domain: domain.value,
    })

    // 保存结果
    resultFilename.value = proofreadRes.filename
    correctedDownloadUrl.value = proofreadRes.corrected_download_url || ''
    issues.value = proofreadRes.issues.map((i: any) => ({
      ...i,
      _accepted: false,
      _ignored: false,
    }))

    progress.value = 100
    proofreading.value = false
    step.value = 'result'

    if (proofreadRes.total_issues === 0) {
      ElMessage.success('文档没有发现任何问题')
    } else {
      ElMessage.info(`共发现 ${proofreadRes.total_issues} 个问题，请逐条审阅`)
    }
  } catch (e: any) {
    step.value = 'upload'
    uploading.value = false
    proofreading.value = false
    progress.value = 0
  }
}

// 接受单条修改
function acceptIssue(issue: IssueWithStatus) {
  if (issue.original && issue.suggestion) {
    currentText.value = currentText.value.replace(issue.original, issue.suggestion)
    if (currentHtml.value) {
      currentHtml.value = replaceTextInHtml(currentHtml.value, issue.original, escapeHtml(issue.suggestion))
    }
  }
  issue._accepted = true
}

// 忽略
function ignoreIssue(issue: IssueWithStatus) {
  issue._ignored = true
}

// 撤销
function undoIssue(issue: IssueWithStatus) {
  if (issue._accepted && issue.original && issue.suggestion) {
    currentText.value = currentText.value.replace(issue.suggestion, issue.original)
    if (currentHtml.value) {
      currentHtml.value = replaceTextInHtml(currentHtml.value, issue.suggestion, escapeHtml(issue.original))
    }
  }
  issue._accepted = false
  issue._ignored = false
}

// 一键修改全部
async function handleAcceptAll() {
  try {
    await ElMessageBox.confirm(
      `确认接受全部 ${pendingCount.value} 条修改建议？`,
      '一键修改',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    for (const issue of issues.value) {
      if (!issue._accepted && !issue._ignored && issue.original && issue.suggestion) {
        currentText.value = currentText.value.replace(issue.original, issue.suggestion)
        if (currentHtml.value) {
          currentHtml.value = replaceTextInHtml(currentHtml.value, issue.original, escapeHtml(issue.suggestion))
        }
        issue._accepted = true
      }
    }
    ElMessage.success('已接受所有修改')
  } catch {
    // 取消
  }
}

// 下载修订文档
function downloadCorrected() {
  if (correctedDownloadUrl.value) {
    window.open(correctedDownloadUrl.value, '_blank')
  }
}

// 导出修订文本
function handleExportText() {
  const blob = new Blob([currentText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `修订_${resultFilename.value || 'document'}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('修订文本已导出')
}

// 导出问题报告
function handleExportReport() {
  if (issues.value.length === 0) return
  const lines = [
    `文档校对报告 - ${resultFilename.value}`,
    `共发现 ${issues.value.length} 个问题`,
    `已接受: ${acceptedCount.value}  已忽略: ${issues.value.filter(i => i._ignored).length}  待处理: ${pendingCount.value}`,
    '',
  ]
  issues.value.forEach((issue, i) => {
    const status = issue._accepted ? '[已接受]' : issue._ignored ? '[已忽略]' : '[待处理]'
    lines.push(`${i + 1}. ${status} [${typeLabel(issue.type)}] ${severityLabel(issue.severity)}`)
    lines.push(`   原文: ${issue.original}`)
    lines.push(`   建议: ${issue.suggestion}`)
    if (issue.explanation) lines.push(`   说明: ${issue.explanation}`)
    lines.push('')
  })
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `校对报告_${resultFilename.value || 'document'}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

// 重置
function resetAll() {
  step.value = 'upload'
  selectedFile.value = null
  originalText.value = ''
  currentText.value = ''
  currentHtml.value = ''
  resultFilename.value = ''
  correctedDownloadUrl.value = ''
  issues.value = []
  progress.value = 0
  filterType.value = ''
}
</script>

<style scoped lang="scss">
.document-proofread-page {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  .card-title { font-size: 18px; font-weight: 600; }
}

.upload-dragger {
  width: 100%;
  margin-bottom: 20px;
  :deep(.el-upload-dragger) {
    padding: 40px 20px;
  }
  .upload-icon {
    font-size: 48px;
    color: var(--color-text-secondary);
    margin-bottom: 12px;
  }
}

.upload-tip {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 8px;
}

.proofread-settings {
  padding: 16px;
  background: #fafafa;
  border-radius: var(--border-radius-md);

  .file-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding: 8px 12px;
    background: #fff;
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--color-border);
  }

  .setting-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    .setting-label {
      width: 80px;
      font-weight: 500;
      flex-shrink: 0;
    }
  }
}

.processing-section {
  .processing-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 20px;
    .processing-icon { color: var(--color-primary); margin-bottom: 16px; animation: spin 1.5s linear infinite; }
    h3 { margin-bottom: 8px; }
    .processing-info { color: var(--color-text-secondary); font-size: 14px; }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 结果区域 */
.result-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;

  .toolbar-info {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .toolbar-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
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

  .text-count {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.original-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text);
  word-break: break-all;

  :deep(p) {
    margin: 0.3em 0;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 0.5em 0 0.3em;
    font-weight: 600;
  }

  :deep(h1) { font-size: 22pt; }
  :deep(h2) { font-size: 18pt; }
  :deep(h3) { font-size: 14pt; }
  :deep(h4) { font-size: 12pt; }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
  }

  :deep(td), :deep(th) {
    border: 1px solid #ccc;
    padding: 6px 8px;
  }

  :deep(strong) { font-weight: 700; }
  :deep(em) { font-style: italic; }
  :deep(u) { text-decoration: underline; }
  :deep(s) { text-decoration: line-through; }
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
    gap: 6px;
    margin-bottom: 10px;
    align-items: center;

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
    .setting-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
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
