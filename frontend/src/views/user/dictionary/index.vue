<template>
  <div class="dictionary-page">
    <!-- 词库列表 -->
    <el-card v-if="!currentDict" class="dict-list-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">个性化词库管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>新建词库
          </el-button>
        </div>
      </template>

      <el-table :data="dictionaries" v-loading="loading" stripe>
        <el-table-column prop="name" label="词库名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="entry_count" label="词条数" width="100" align="center" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="handleToggleActive(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDict(row)">管理词条</el-button>
            <el-button type="warning" link size="small" @click="editDict(row)">编辑</el-button>
            <el-popconfirm title="确定删除该词库？" @confirm="handleDeleteDict(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && dictionaries.length === 0" description="暂无自定义词库" />
    </el-card>

    <!-- 词条管理 -->
    <div v-else class="entry-section">
      <div class="entry-toolbar">
        <el-button @click="currentDict = null"><el-icon><Back /></el-icon>返回词库列表</el-button>
        <span class="dict-name">{{ currentDict.name }}</span>
        <el-tag>{{ entries.length }} 条词条</el-tag>
        <div style="margin-left: auto; display: flex; gap: 8px;">
          <el-button type="primary" size="small" @click="showAddEntry = true">
            <el-icon><Plus /></el-icon>添加词条
          </el-button>
          <el-button size="small" @click="showBatchImport = true">批量导入</el-button>
        </div>
      </div>

      <el-card>
        <el-input v-model="entryKeyword" placeholder="搜索词条..." clearable style="width: 260px; margin-bottom: 12px;" @input="fetchEntries" />
        <el-table :data="entries" v-loading="entryLoading" stripe>
          <el-table-column prop="wrong_word" label="错误词" min-width="150">
            <template #default="{ row }">
              <span style="color: #f56c6c; font-weight: 500;">{{ row.wrong_word }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="correct_word" label="正确词" min-width="150">
            <template #default="{ row }">
              <span style="color: #67c23a; font-weight: 500;">{{ row.correct_word }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-popconfirm title="确定删除？" @confirm="handleDeleteEntry(row.id)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!entryLoading && entries.length === 0" description="暂无词条" />
      </el-card>
    </div>

    <!-- 新建/编辑词库弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingDict ? '编辑词库' : '新建词库'" width="420px" @close="resetDictForm">
      <el-form :model="dictForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="dictForm.name" placeholder="词库名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="dictForm.description" type="textarea" placeholder="词库描述（可选）" :rows="3" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveDict">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加词条弹窗 -->
    <el-dialog v-model="showAddEntry" title="添加词条" width="420px" @close="resetEntryForm">
      <el-form :model="entryForm" label-width="80px">
        <el-form-item label="错误词" required>
          <el-input v-model="entryForm.wrong_word" placeholder="输入错误词" maxlength="200" />
        </el-form-item>
        <el-form-item label="正确词" required>
          <el-input v-model="entryForm.correct_word" placeholder="输入正确词" maxlength="200" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="entryForm.remark" placeholder="备注（可选）" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEntry = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleAddEntry">添加</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showBatchImport" title="批量导入词条" width="520px">
      <p style="margin-bottom: 8px; color: #666; font-size: 13px;">每行一条，格式：错误词,正确词,备注（备注可选）</p>
      <el-input v-model="batchText" type="textarea" :rows="10" placeholder="错误词1,正确词1,备注1&#10;错误词2,正确词2" />
      <template #footer>
        <el-button @click="showBatchImport = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleBatchImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listDictionariesApi, createDictionaryApi, updateDictionaryApi, deleteDictionaryApi,
  listEntriesApi, createEntryApi, batchCreateEntriesApi, deleteEntryApi,
  type DictionaryItem, type EntryItem,
} from '@/api/dictionary'

const loading = ref(false)
const saving = ref(false)
const dictionaries = ref<DictionaryItem[]>([])
const currentDict = ref<DictionaryItem | null>(null)
const editingDict = ref<DictionaryItem | null>(null)

const showCreateDialog = ref(false)
const dictForm = ref({ name: '', description: '' })

// 词条
const entries = ref<EntryItem[]>([])
const entryLoading = ref(false)
const entryKeyword = ref('')
const showAddEntry = ref(false)
const entryForm = ref({ wrong_word: '', correct_word: '', remark: '' })
const showBatchImport = ref(false)
const batchText = ref('')

onMounted(() => fetchDictionaries())

async function fetchDictionaries() {
  loading.value = true
  try { dictionaries.value = await listDictionariesApi() } catch {}
  loading.value = false
}

async function handleSaveDict() {
  if (!dictForm.value.name.trim()) return ElMessage.warning('请输入词库名称')
  saving.value = true
  try {
    if (editingDict.value) {
      await updateDictionaryApi(editingDict.value.id, dictForm.value)
      ElMessage.success('词库已更新')
    } else {
      await createDictionaryApi(dictForm.value)
      ElMessage.success('词库已创建')
    }
    showCreateDialog.value = false
    resetDictForm()
    await fetchDictionaries()
  } catch {}
  saving.value = false
}

function editDict(row: DictionaryItem) {
  editingDict.value = row
  dictForm.value = { name: row.name, description: row.description || '' }
  showCreateDialog.value = true
}

function resetDictForm() {
  editingDict.value = null
  dictForm.value = { name: '', description: '' }
}

async function handleToggleActive(row: DictionaryItem) {
  try { await updateDictionaryApi(row.id, { is_active: row.is_active }) } catch { row.is_active = !row.is_active }
}

async function handleDeleteDict(id: number) {
  try {
    await deleteDictionaryApi(id)
    ElMessage.success('词库已删除')
    await fetchDictionaries()
  } catch {}
}

async function openDict(row: DictionaryItem) {
  currentDict.value = row
  await fetchEntries()
}

async function fetchEntries() {
  if (!currentDict.value) return
  entryLoading.value = true
  try {
    entries.value = await listEntriesApi(currentDict.value.id, {
      keyword: entryKeyword.value || undefined,
      page_size: 200,
    })
  } catch {}
  entryLoading.value = false
}

async function handleAddEntry() {
  if (!entryForm.value.wrong_word.trim() || !entryForm.value.correct_word.trim()) {
    return ElMessage.warning('请填写错误词和正确词')
  }
  saving.value = true
  try {
    await createEntryApi(currentDict.value!.id, entryForm.value)
    ElMessage.success('词条已添加')
    showAddEntry.value = false
    resetEntryForm()
    await fetchEntries()
    currentDict.value!.entry_count++
  } catch {}
  saving.value = false
}

function resetEntryForm() {
  entryForm.value = { wrong_word: '', correct_word: '', remark: '' }
}

async function handleDeleteEntry(entryId: number) {
  try {
    await deleteEntryApi(currentDict.value!.id, entryId)
    ElMessage.success('词条已删除')
    await fetchEntries()
    currentDict.value!.entry_count = Math.max(0, currentDict.value!.entry_count - 1)
  } catch {}
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  if (lines.length === 0) return ElMessage.warning('请输入词条数据')

  const parsed = lines.map(line => {
    const parts = line.split(',').map(s => s.trim())
    return { wrong_word: parts[0] || '', correct_word: parts[1] || '', remark: parts[2] || '' }
  }).filter(e => e.wrong_word && e.correct_word)

  if (parsed.length === 0) return ElMessage.warning('未解析到有效词条')

  saving.value = true
  try {
    const res = await batchCreateEntriesApi(currentDict.value!.id, parsed)
    ElMessage.success(`成功导入 ${res.count} 条词条`)
    showBatchImport.value = false
    batchText.value = ''
    await fetchEntries()
    await fetchDictionaries()
  } catch {}
  saving.value = false
}
</script>

<style scoped lang="scss">
.dictionary-page { max-width: 1100px; margin: 0 auto; }

.card-header {
  display: flex; align-items: center; justify-content: space-between;
  .card-title { font-size: 18px; font-weight: 600; }
}

.entry-toolbar {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 16px; padding: 12px 16px;
  background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  .dict-name { font-size: 16px; font-weight: 600; }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .entry-toolbar {
    flex-wrap: wrap;
  }
}
</style>
