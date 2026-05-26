<template>
  <div class="whitelist-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">放行词管理</span>
          <div style="display: flex; gap: 8px;">
            <el-button type="primary" size="small" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>添加放行词
            </el-button>
            <el-button size="small" @click="showBatchDialog = true">批量导入</el-button>
          </div>
        </div>
      </template>

      <el-input v-model="keyword" placeholder="搜索放行词..." clearable style="width: 260px; margin-bottom: 12px;" @input="fetchList" />

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="word" label="放行词" min-width="150">
          <template #default="{ row }">
            <span style="font-weight: 500; color: #67c23a;">{{ row.word }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'permanent' ? 'success' : 'warning'" size="small">
              {{ row.type === 'permanent' ? '永久' : '临时' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column label="过期时间" width="170">
          <template #default="{ row }">
            <span v-if="row.expire_at" style="font-size: 12px; color: #999;">{{ row.expire_at }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editWord(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无放行词" />
    </el-card>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="showAddDialog" :title="editingItem ? '编辑放行词' : '添加放行词'" width="420px" @close="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="放行词" required>
          <el-input v-model="form.word" placeholder="输入放行词" maxlength="200" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio value="permanent">永久</el-radio>
            <el-radio value="temporary">临时</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="过期时间" v-if="form.type === 'temporary'">
          <el-date-picker v-model="form.expire_at" type="datetime" placeholder="选择过期时间" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" placeholder="备注（可选）" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showBatchDialog" title="批量导入放行词" width="480px">
      <p style="margin-bottom: 8px; color: #666; font-size: 13px;">每行一个放行词，可选格式：放行词,备注</p>
      <el-input v-model="batchText" type="textarea" :rows="10" placeholder="放行词1&#10;放行词2,备注" />
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleBatchImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listWhitelistApi, createWhitelistApi, updateWhitelistApi, deleteWhitelistApi, batchCreateWhitelistApi,
  type WhitelistItem,
} from '@/api/whitelist'

const loading = ref(false)
const saving = ref(false)
const list = ref<WhitelistItem[]>([])
const keyword = ref('')

const showAddDialog = ref(false)
const showBatchDialog = ref(false)
const editingItem = ref<WhitelistItem | null>(null)
const form = ref({ word: '', type: 'permanent', remark: '', expire_at: '' as string | null })
const batchText = ref('')

onMounted(() => fetchList())

async function fetchList() {
  loading.value = true
  try { list.value = await listWhitelistApi({ keyword: keyword.value || undefined, page_size: 200 }) } catch {}
  loading.value = false
}

function editWord(row: WhitelistItem) {
  editingItem.value = row
  form.value = { word: row.word, type: row.type, remark: row.remark || '', expire_at: row.expire_at || null }
  showAddDialog.value = true
}

function resetForm() {
  editingItem.value = null
  form.value = { word: '', type: 'permanent', remark: '', expire_at: null }
}

async function handleSave() {
  if (!form.value.word.trim()) return ElMessage.warning('请输入放行词')
  saving.value = true
  try {
    const payload: any = { ...form.value }
    if (payload.type === 'permanent') payload.expire_at = null
    if (editingItem.value) {
      await updateWhitelistApi(editingItem.value.id, payload)
      ElMessage.success('放行词已更新')
    } else {
      await createWhitelistApi(payload)
      ElMessage.success('放行词已添加')
    }
    showAddDialog.value = false
    resetForm()
    await fetchList()
  } catch {}
  saving.value = false
}

async function handleDelete(id: number) {
  try {
    await deleteWhitelistApi(id)
    ElMessage.success('放行词已删除')
    await fetchList()
  } catch {}
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  if (lines.length === 0) return ElMessage.warning('请输入放行词')
  const parsed = lines.map(line => {
    const parts = line.split(',').map(s => s.trim())
    return { word: parts[0], remark: parts[1] || '' }
  }).filter(e => e.word)
  if (parsed.length === 0) return ElMessage.warning('未解析到有效放行词')
  saving.value = true
  try {
    const res = await batchCreateWhitelistApi(parsed)
    ElMessage.success(`成功导入 ${res.count} 个放行词`)
    showBatchDialog.value = false
    batchText.value = ''
    await fetchList()
  } catch {}
  saving.value = false
}
</script>

<style scoped lang="scss">
.whitelist-page { max-width: 1100px; margin: 0 auto; }
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  .card-title { font-size: 18px; font-weight: 600; }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
