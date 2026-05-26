<template>
  <div class="admin-global-dict">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" style="color: #333;">{{ stats.total }}</div>
        <div class="stat-label">词条总数</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" style="color: #f56c6c;">{{ stats.sensitive_count }}</div>
        <div class="stat-label">敏感词</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" style="color: #e6a23c;">{{ stats.banned_count }}</div>
        <div class="stat-label">禁词</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" style="color: #0056b3;">{{ stats.correction_count }}</div>
        <div class="stat-label">纠错词条</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value" style="color: #67c23a;">{{ stats.whitelist_count }}</div>
        <div class="stat-label">放行词</div>
      </el-card>
    </div>

    <!-- 主体表格 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">全局词库管理</span>
          <div style="display: flex; gap: 8px;">
            <el-button type="primary" size="small" @click="openAddDialog"><el-icon><Plus /></el-icon>添加词条</el-button>
            <el-button size="small" @click="showBatchDialog = true">批量导入</el-button>
          </div>
        </div>
      </template>

      <!-- 过滤工具栏 -->
      <div style="display: flex; gap: 12px; margin-bottom: 12px; align-items: center;">
        <el-radio-group v-model="filterType" size="small" @change="fetchList">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="sensitive">敏感词</el-radio-button>
          <el-radio-button value="banned">禁词</el-radio-button>
          <el-radio-button value="correction">纠错词条</el-radio-button>
          <el-radio-button value="whitelist">放行词</el-radio-button>
        </el-radio-group>
        <el-input v-model="keyword" placeholder="搜索词条..." clearable style="width: 200px;" @input="onSearch" />
      </div>

      <el-table :data="wordList" stripe v-loading="loading" max-height="500">
        <el-table-column prop="word" label="词条" min-width="140">
          <template #default="{ row }">
            <span :style="{ fontWeight: 500, color: typeColorMap[row.type] || '#333' }">{{ row.word }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type] || 'info'" size="small">{{ typeLabelMap[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="replacement" label="替换词" width="130">
          <template #default="{ row }">
            <span v-if="row.replacement" style="color: #67c23a;">→ {{ row.replacement }}</span>
            <span v-else style="color: #ccc;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" show-overflow-tooltip />
        <el-table-column prop="severity" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'error' ? 'danger' : row.severity === 'warning' ? 'warning' : 'info'" size="small">
              {{ ({ error: '严重', warning: '警告', info: '提示' } as Record<string, string>)[row.severity] || row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除该词条？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && wordList.length === 0" description="暂无词条数据" />

      <!-- 分页 -->
      <div style="display: flex; justify-content: flex-end; margin-top: 12px;" v-if="wordList.length > 0">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="wordList.length >= pageSize ? (page + 1) * pageSize : page * pageSize"
          layout="prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="showFormDialog" :title="editingId ? '编辑词条' : '添加词条'" width="500px" destroy-on-close>
      <el-form :model="formData" label-width="80px">
        <el-form-item label="词条" required>
          <el-input v-model="formData.word" placeholder="请输入词条" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="formData.type">
            <el-radio value="sensitive">敏感词</el-radio>
            <el-radio value="banned">禁词</el-radio>
            <el-radio value="correction">纠错词条</el-radio>
            <el-radio value="whitelist">放行词</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="替换词" v-if="formData.type === 'correction'">
          <el-input v-model="formData.replacement" placeholder="正确的写法" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="formData.category" placeholder="如：政治、粗俗用语、公文用语 等" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-radio-group v-model="formData.severity">
            <el-radio value="error">严重</el-radio>
            <el-radio value="warning">警告</el-radio>
            <el-radio value="info">提示</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="备注说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ editingId ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showBatchDialog" title="批量导入词条" width="560px" destroy-on-close>
      <el-alert type="info" :closable="false" style="margin-bottom: 12px;">
        <template #title>
          <div style="font-size: 13px;">
            每行一条，格式：<b>词条,类型,替换词,分类,备注</b><br/>
            类型可选：sensitive / banned / correction / whitelist<br/>
            示例：<code>帐号,correction,账号,常见错别字,帐→账</code>
          </div>
        </template>
      </el-alert>
      <el-input v-model="batchText" type="textarea" :rows="10" placeholder="帐号,correction,账号,常见错别字,帐→账&#10;卧槽,banned,,粗俗用语,正式文档禁用&#10;API,whitelist,,技术术语,无需校对" />
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleBatchImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  type GlobalWordItem, type GlobalWordStats,
  getGlobalWordStatsApi, listGlobalWordsApi,
  createGlobalWordApi, updateGlobalWordApi,
  deleteGlobalWordApi, batchCreateGlobalWordsApi,
} from '@/api/admin'

const typeLabelMap: Record<string, string> = { sensitive: '敏感词', banned: '禁词', correction: '纠错词条', whitelist: '放行词' }
const typeTagMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = { sensitive: 'danger', banned: 'warning', correction: '', whitelist: 'success' }
const typeColorMap: Record<string, string> = { sensitive: '#f56c6c', banned: '#e6a23c', correction: '#0056b3', whitelist: '#67c23a' }

const loading = ref(false)
const submitting = ref(false)
const wordList = ref<GlobalWordItem[]>([])
const stats = reactive<GlobalWordStats>({ total: 0, sensitive_count: 0, banned_count: 0, whitelist_count: 0, correction_count: 0 })
const keyword = ref('')
const filterType = ref('')
const page = ref(1)
const pageSize = 50

const showFormDialog = ref(false)
const showBatchDialog = ref(false)
const editingId = ref<number | null>(null)
const formData = reactive({ word: '', type: 'sensitive', replacement: '', category: '', severity: 'error', remark: '' })
const batchText = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  fetchStats()
  fetchList()
})

async function fetchStats() {
  try {
    const data = await getGlobalWordStatsApi()
    Object.assign(stats, data)
  } catch (e) { /* 静默 */ }
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filterType.value) params.type = filterType.value
    if (keyword.value) params.keyword = keyword.value
    wordList.value = await listGlobalWordsApi(params)
  } catch (e) {
    ElMessage.error('加载词库失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; fetchList() }, 300)
}

function openAddDialog() {
  editingId.value = null
  Object.assign(formData, { word: '', type: 'sensitive', replacement: '', category: '', severity: 'error', remark: '' })
  showFormDialog.value = true
}

function openEditDialog(row: GlobalWordItem) {
  editingId.value = row.id
  Object.assign(formData, {
    word: row.word, type: row.type, replacement: row.replacement || '',
    category: row.category || '', severity: row.severity, remark: row.remark || '',
  })
  showFormDialog.value = true
}

async function handleSubmit() {
  if (!formData.word.trim()) return ElMessage.warning('请输入词条')
  submitting.value = true
  try {
    if (editingId.value) {
      await updateGlobalWordApi(editingId.value, { ...formData })
      ElMessage.success('词条已更新')
    } else {
      await createGlobalWordApi({ ...formData })
      ElMessage.success('词条已添加')
    }
    showFormDialog.value = false
    fetchStats()
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteGlobalWordApi(id)
    ElMessage.success('已删除')
    fetchStats()
    fetchList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  if (!lines.length) return ElMessage.warning('请输入要导入的词条')

  const entries = lines.map(line => {
    const parts = line.split(',').map(s => s.trim())
    return {
      word: parts[0] || '',
      type: parts[1] || 'sensitive',
      replacement: parts[2] || undefined,
      category: parts[3] || undefined,
      severity: 'warning',
      remark: parts[4] || undefined,
    }
  }).filter(e => e.word)

  submitting.value = true
  try {
    const res = await batchCreateGlobalWordsApi({ entries })
    ElMessage.success(`导入完成：新增 ${res.added} 条，跳过 ${res.skipped} 条重复`)
    showBatchDialog.value = false
    batchText.value = ''
    fetchStats()
    fetchList()
  } catch (e) {
    ElMessage.error('批量导入失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.admin-global-dict {
  .stats-row {
    display: flex; gap: 12px; margin-bottom: 16px;
    .stat-card {
      flex: 1; text-align: center;
      .stat-value { font-size: 28px; font-weight: 700; line-height: 1.4; }
      .stat-label { font-size: 13px; color: #999; margin-top: 2px; }
    }
  }
  .card-header { display: flex; align-items: center; justify-content: space-between; .card-title { font-size: 16px; font-weight: 600; color: #333; } }
}
</style>
