<template>
  <div class="history-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">校对历史</span>
          <div class="header-filters">
            <el-select v-model="filterType" placeholder="全部类型" clearable size="small" style="width: 120px;" @change="fetchList">
              <el-option label="全部" value="" />
              <el-option label="AI润色" value="polish" />
              <el-option label="文本校对" value="text" />
              <el-option label="文档校对" value="document" />
            </el-select>
            <el-select v-model="filterDomain" placeholder="全部领域" clearable size="small" style="width: 120px;" @change="fetchList">
              <el-option label="全部" value="" />
              <el-option label="通用" value="general" />
              <el-option label="公文" value="official" />
              <el-option label="法律" value="legal" />
              <el-option label="电力" value="power" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="items" v-loading="loading" stripe @row-click="openDetail">
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="recordTypeTag(row.type)" size="small">
              {{ recordTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容预览" min-width="300">
          <template #default="{ row }">
            <div class="preview-text">{{ row.text_preview }}</div>
            <div v-if="row.source_filename" class="filename-tag">
              <el-tag size="small" type="info">{{ row.source_filename }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="domain" label="领域" width="80" align="center">
          <template #default="{ row }">{{ domainLabel(row.domain) }}</template>
        </el-table-column>
        <el-table-column prop="total_issues" label="问题数" width="80" align="center">
          <template #default="{ row }">
            <template v-if="row.type === 'polish'">
              <span style="font-size: 12px; color: #999;">-</span>
            </template>
            <template v-else>
              <el-tag :type="row.total_issues > 0 ? 'danger' : 'success'" size="small">{{ row.total_issues }}</el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="Token" width="100" align="center">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #999;">{{ row.token_usage?.total_tokens || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #999;">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-popconfirm title="确定删除此记录？" @confirm.stop="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && items.length === 0" description="暂无校对历史" />

      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detail?.type === 'polish' ? '润色详情' : '校对详情'" size="600px" direction="rtl">
      <template v-if="detail">
        <div class="detail-meta">
          <el-tag :type="recordTypeTag(detail.type)">{{ recordTypeLabel(detail.type) }}</el-tag>
          <el-tag type="info">{{ detail.type === 'polish' ? polishStyleLabel(detail.domain) : domainLabel(detail.domain) }}</el-tag>
          <template v-if="detail.type !== 'polish'">
            <el-tag :type="detail.total_issues > 0 ? 'danger' : 'success'">{{ detail.total_issues }} 个问题</el-tag>
          </template>
          <span v-if="detail.source_filename" style="font-size: 13px; color: #666;">{{ detail.source_filename }}</span>
        </div>

        <el-divider content-position="left">原文</el-divider>
        <div class="detail-text">{{ detail.original_text }}</div>

        <!-- AI润色结果 -->
        <template v-if="detail.type === 'polish'">
          <el-divider content-position="left">润色结果</el-divider>
          <div class="polish-versions">
            <div v-for="(ver, i) in (detail.result?.versions || [])" :key="i" class="polish-version-item">
              <div class="version-label">
                <el-tag size="small">{{ ver.label }}</el-tag>
              </div>
              <div class="version-content">{{ ver.content }}</div>
            </div>
            <div v-if="!detail.result?.versions?.length && detail.modified_text" class="detail-text" style="white-space: pre-wrap;">{{ detail.modified_text }}</div>
          </div>
        </template>

        <!-- 校对问题列表 -->
        <template v-else>
          <el-divider content-position="left">问题列表 ({{ detail.result?.issues?.length || 0 }})</el-divider>
          <div class="detail-issues">
            <div v-for="(issue, i) in (detail.result?.issues || [])" :key="i" class="issue-item">
              <div class="issue-head">
                <el-tag :type="severityColor(issue.severity)" size="small">{{ typeLabel(issue.type) }}</el-tag>
                <el-tag :type="severityColor(issue.severity)" size="small" effect="plain">{{ severityLabel(issue.severity) }}</el-tag>
              </div>
              <div class="issue-body">
                <div><span class="label">原文：</span><span class="text-del">{{ issue.original }}</span></div>
                <div><span class="label">建议：</span><span class="text-add">{{ issue.suggestion }}</span></div>
                <div v-if="issue.explanation"><span class="label">说明：</span><span class="text-muted">{{ issue.explanation }}</span></div>
              </div>
            </div>
            <el-empty v-if="!detail.result?.issues?.length" description="无问题" :image-size="60" />
          </div>
        </template>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listHistoryApi, getHistoryDetailApi, deleteHistoryApi,
  type HistoryItem, type HistoryDetail,
} from '@/api/history'

const loading = ref(false)
const items = ref<HistoryItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterType = ref('')
const filterDomain = ref('')

const showDetail = ref(false)
const detail = ref<HistoryDetail | null>(null)

onMounted(() => fetchList())

async function fetchList() {
  loading.value = true
  try {
    const res = await listHistoryApi({
      page: page.value,
      page_size: pageSize,
      type: filterType.value || undefined,
      domain: filterDomain.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } catch {}
  loading.value = false
}

async function openDetail(row: HistoryItem) {
  try {
    detail.value = await getHistoryDetailApi(row.id)
    showDetail.value = true
  } catch {}
}

async function handleDelete(id: number) {
  try {
    await deleteHistoryApi(id)
    ElMessage.success('记录已删除')
    await fetchList()
  } catch {}
}

function formatTime(t?: string): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function domainLabel(d: string): string {
  const m: Record<string, string> = { general: '通用', official: '公文', legal: '法律', power: '电力', new_energy: '新能源', meter: '电能表' }
  return m[d] || d
}

function typeLabel(t: string): string {
  const m: Record<string, string> = { typo: '错别字', grammar: '语法', punctuation: '标点', style: '表达', sensitive: '敏感词', logic: '逻辑' }
  return m[t] || t
}

function severityColor(s: string): 'danger' | 'warning' | 'info' | 'success' | 'primary' {
  switch (s) { case 'error': return 'danger'; case 'warning': return 'warning'; default: return 'info' }
}

function severityLabel(s: string): string {
  switch (s) { case 'error': return '错误'; case 'warning': return '警告'; default: return '建议' }
}

function recordTypeLabel(t: string): string {
  switch (t) { case 'polish': return 'AI润色'; case 'text': return '文本校对'; case 'document': return '文档校对'; default: return t }
}

function recordTypeTag(t: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  switch (t) { case 'polish': return 'warning'; case 'text': return 'primary'; case 'document': return 'success'; default: return 'info' }
}

function polishStyleLabel(style: string): string {
  const m: Record<string, string> = {
    formal: '正式规范', friendly: '亲切友好', plain: '通俗易懂', concise: '精简凝练',
    evidence: '论证严谨', strategic: '战略性', practical: '务实实用',
    firm: '坚定有力', gentle: '柔和委婉', action: '行动号召'
  }
  return m[style] || style
}
</script>

<style scoped lang="scss">
.history-page { max-width: 1200px; margin: 0 auto; }

.card-header {
  display: flex; align-items: center; justify-content: space-between;
  .card-title { font-size: 18px; font-weight: 600; }
  .header-filters { display: flex; gap: 8px; }
}

.preview-text {
  font-size: 13px; color: #333; line-height: 1.5;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 400px;
}
.filename-tag { margin-top: 4px; }

.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }

.detail-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
.detail-text {
  background: #f9f9f9; padding: 12px; border-radius: 6px;
  font-size: 13px; line-height: 1.8; white-space: pre-wrap; max-height: 200px; overflow-y: auto;
}

.detail-issues {
  .issue-item {
    padding: 10px; border: 1px solid #eee; border-radius: 6px; margin-bottom: 8px;
    &:hover { box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
  }
  .issue-head { display: flex; gap: 6px; margin-bottom: 6px; }
  .issue-body {
    font-size: 13px; line-height: 1.7;
    .label { color: #999; font-weight: 500; }
    .text-del { color: #f56c6c; text-decoration: line-through; }
    .text-add { color: #67c23a; font-weight: 500; }
    .text-muted { color: #999; font-size: 12px; }
  }
}

.polish-versions {
  .polish-version-item {
    margin-bottom: 16px;
    padding: 12px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;

    .version-label {
      margin-bottom: 8px;
    }

    .version-content {
      font-size: 13px;
      line-height: 1.8;
      color: #333;
      white-space: pre-wrap;
    }
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .header-filters {
    width: 100%;
  }
  .preview-text {
    max-width: 200px;
  }
}
</style>
