<template>
  <div class="audit-page">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card v-for="s in statCards" :key="s.label" class="stat-card" shadow="hover">
        <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </el-card>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent="handleSearch">
        <el-form-item label="操作类型">
          <el-select v-model="filters.action_type" placeholder="全部" clearable style="width: 140px;">
            <el-option label="AI润色" value="polish" />
            <el-option label="文本校对" value="proofread_text" />
            <el-option label="文档校对" value="proofread_doc" />
            <el-option label="查看历史" value="view_history" />
            <el-option label="登录成功" value="login_success" />
            <el-option label="登录失败" value="login_failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户类型">
          <el-select v-model="filters.user_type" placeholder="全部" clearable style="width: 120px;">
            <el-option label="登录用户" value="registered" />
            <el-option label="游客" value="guest" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 100px;">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP">
          <el-input v-model="filters.ip" placeholder="IP地址" clearable style="width: 140px;" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 240px;"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="用户名/工号/内容" clearable style="width: 160px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <el-table :data="logs" v-loading="loading" stripe style="width: 100%;">
        <el-table-column label="时间" width="170" prop="created_at">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action_type)" size="small">
              {{ actionLabel(row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用户" width="140">
          <template #default="{ row }">
            <template v-if="row.is_guest">
              <el-tag type="info" size="small">游客</el-tag>
            </template>
            <template v-else>
              <span style="font-weight: 500;">{{ row.username }}</span>
              <div style="font-size: 11px; color: #999;">{{ row.employee_id }}</div>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="IP地址" width="130" prop="client_ip" />
        <el-table-column label="设备" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.device_type === 'mobile'" title="手机"><Iphone /></el-icon>
            <el-icon v-else-if="row.device_type === 'tablet'" title="平板"><Iphone /></el-icon>
            <el-icon v-else title="桌面"><Monitor /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="内容摘要" min-width="200">
          <template #default="{ row }">
            <div v-if="row.input_preview" class="content-preview">
              <span class="preview-label">输入:</span> {{ row.input_preview }}
            </div>
            <div v-if="row.output_preview" class="content-preview">
              <span class="preview-label">输出:</span> {{ row.output_preview }}
            </div>
            <div v-if="row.file_name" class="content-preview">
              <el-icon><Document /></el-icon> {{ row.file_name }}
            </div>
            <span v-if="!row.input_preview && !row.output_preview && !row.file_name" style="color: #999;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.duration_ms != null">{{ row.duration_ms }}ms</span>
            <span v-else style="color: #999;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetail(row.id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="fetchLogs"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="日志详情" size="560px" destroy-on-close>
      <div v-if="detail" class="detail-content">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="操作类型">
            <el-tag :type="actionTagType(detail.action_type)" size="small">{{ actionLabel(detail.action_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="用户">
            <template v-if="detail.is_guest">游客</template>
            <template v-else>{{ detail.username }} ({{ detail.employee_id }})</template>
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ detail.client_ip }}</el-descriptions-item>
          <el-descriptions-item label="设备类型">{{ deviceLabel(detail.device_type) }}</el-descriptions-item>
          <el-descriptions-item label="User-Agent">
            <span style="font-size: 11px; word-break: break-all;">{{ detail.user_agent || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="操作状态">
            <el-tag :type="detail.status === 'success' ? 'success' : 'danger'" size="small">
              {{ detail.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.duration_ms != null" label="耗时">{{ detail.duration_ms }}ms</el-descriptions-item>
          <el-descriptions-item v-if="detail.error_message" label="错误信息">
            <span style="color: #f56c6c;">{{ detail.error_message }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 额外参数 -->
        <div v-if="detail.extra_params" class="detail-section">
          <h4>操作参数</h4>
          <div class="params-grid">
            <div v-for="(val, key) in detail.extra_params" :key="key" class="param-item">
              <span class="param-key">{{ key }}:</span>
              <span class="param-val">{{ Array.isArray(val) ? val.join(', ') : val }}</span>
            </div>
          </div>
        </div>

        <!-- 文件信息 -->
        <div v-if="detail.file_name" class="detail-section">
          <h4>文件信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="文件名">{{ detail.file_name }}</el-descriptions-item>
            <el-descriptions-item v-if="detail.file_size" label="文件大小">{{ formatSize(detail.file_size) }}</el-descriptions-item>
            <el-descriptions-item v-if="detail.file_id" label="文件ID">{{ detail.file_id }}</el-descriptions-item>
            <el-descriptions-item v-if="detail.file_path" label="服务器路径">
              <span style="font-size: 11px; word-break: break-all;">{{ detail.file_path }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 输入内容 -->
        <div v-if="detail.input_text" class="detail-section">
          <h4>输入内容 <span class="text-count">({{ detail.input_length }}字)</span></h4>
          <div class="text-block">{{ detail.input_text }}</div>
        </div>

        <!-- 输出内容 -->
        <div v-if="detail.output_text" class="detail-section">
          <h4>输出结果 <span class="text-count">({{ detail.output_length }}字)</span></h4>
          <div class="text-block">{{ detail.output_text }}</div>
        </div>

        <!-- Token 用量 -->
        <div v-if="detail.token_usage" class="detail-section">
          <h4>Token 消耗</h4>
          <div class="params-grid">
            <div v-for="(val, key) in detail.token_usage" :key="key" class="param-item">
              <span class="param-key">{{ key }}:</span>
              <span class="param-val">{{ val }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import {
  getAuditLogsApi,
  getAuditLogDetailApi,
  getAuditStatsApi,
  type AuditLogItem,
  type AuditLogDetail,
  type AuditStats,
} from '@/api/audit'

const loading = ref(false)
const logs = ref<AuditLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dateRange = ref<string[]>([])

const filters = reactive({
  action_type: '',
  user_type: '',
  status: '',
  ip: '',
  keyword: '',
})

// 统计
const stats = ref<AuditStats>({
  today_count: 0,
  today_guest_count: 0,
  today_failed_count: 0,
  total_count: 0,
  type_distribution: {},
})

const statCards = computed(() => [
  { label: '今日操作', value: stats.value.today_count, color: '#0056b3' },
  { label: '今日游客操作', value: stats.value.today_guest_count, color: '#f59e0b' },
  { label: '今日失败', value: stats.value.today_failed_count, color: '#ef4444' },
  { label: '总操作数', value: stats.value.total_count, color: '#333' },
])

// 详情
const detailVisible = ref(false)
const detail = ref<AuditLogDetail | null>(null)

onMounted(() => {
  fetchLogs()
  fetchStats()
})

async function fetchLogs() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filters.action_type) params.action_type = filters.action_type
    if (filters.user_type) params.user_type = filters.user_type
    if (filters.status) params.status = filters.status
    if (filters.ip) params.ip = filters.ip
    if (filters.keyword) params.keyword = filters.keyword
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await getAuditLogsApi(params)
    logs.value = res.items
    total.value = res.total
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    stats.value = await getAuditStatsApi()
  } catch {}
}

function handleSearch() {
  page.value = 1
  fetchLogs()
}

function resetFilters() {
  filters.action_type = ''
  filters.user_type = ''
  filters.status = ''
  filters.ip = ''
  filters.keyword = ''
  dateRange.value = []
  handleSearch()
}

async function showDetail(id: number) {
  try {
    detail.value = await getAuditLogDetailApi(id)
    detailVisible.value = true
  } catch {}
}

// 工具函数
const ACTION_LABELS: Record<string, string> = {
  polish: 'AI润色',
  proofread_text: '文本校对',
  proofread_doc: '文档校对',
  view_history: '查看历史',
  login_success: '登录成功',
  login_failed: '登录失败',
  logout: '退出登录',
}

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

const ACTION_TAG_TYPES: Record<string, TagType> = {
  polish: 'primary',
  proofread_text: 'success',
  proofread_doc: 'warning',
  view_history: 'info',
  login_success: 'success',
  login_failed: 'danger',
  logout: 'info',
}

function actionLabel(type: string): string {
  return ACTION_LABELS[type] || type
}

function actionTagType(type: string): TagType {
  return ACTION_TAG_TYPES[type] || 'info'
}

function deviceLabel(type: string | null): string {
  switch (type) {
    case 'mobile': return '手机'
    case 'tablet': return '平板'
    case 'desktop': return '桌面'
    default: return '未知'
  }
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}
</script>

<style scoped lang="scss">
.audit-page {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;

  .stat-card {
    text-align: center;

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      line-height: 1.4;
    }

    .stat-label {
      font-size: 13px;
      color: #6b7280;
      margin-top: 4px;
    }
  }
}

.filter-card {
  margin-bottom: 16px;

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
}

.content-preview {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;

  .preview-label {
    color: #999;
    font-weight: 500;
  }
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 详情抽屉 */
.detail-content {
  padding: 0 4px;
}

.detail-section {
  margin-top: 20px;

  h4 {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
    border-left: 3px solid #0056b3;
    padding-left: 8px;

    .text-count {
      font-weight: 400;
      font-size: 12px;
      color: #999;
    }
  }
}

.text-block {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.params-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .param-item {
    background: #f3f4f6;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 13px;

    .param-key {
      color: #6b7280;
      margin-right: 4px;
    }

    .param-val {
      font-weight: 500;
      color: #333;
    }
  }
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .filter-form {
    flex-direction: column;
  }
}
</style>
