<template>
  <div class="admin-documents">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span style="font-weight: 600;">文档管理</span>
          <el-tag type="info" size="small">支持 .doc / .docx / .pdf / .txt，最大 20MB</el-tag>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="toolbar" style="display: flex; gap: 12px; margin-bottom: 16px;">
        <el-input
          v-model="keyword"
          placeholder="搜索文件名或上传者"
          clearable
          style="width: 260px;"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filterExt" placeholder="文件类型" clearable style="width: 140px;" @change="handleSearch">
          <el-option label=".doc" value=".doc" />
          <el-option label=".docx" value=".docx" />
          <el-option label=".pdf" value=".pdf" />
          <el-option label=".txt" value=".txt" />
        </el-select>
        <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
      </div>

      <!-- 文档列表 -->
      <el-table :data="documents" stripe v-loading="loading" style="width: 100%;">
        <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
        <el-table-column prop="file_ext" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="extTagType(row.file_ext)">{{ row.file_ext }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100" align="center">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="文本字数" width="100" align="center">
          <template #default="{ row }">{{ row.text_length.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="username" label="上传者" width="120" />
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>下载
            </el-button>
            <el-popconfirm title="确定删除该文档？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button type="danger" link size="small"><el-icon><Delete /></el-icon>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && documents.length === 0" description="暂无上传文件记录" />

      <!-- 分页 -->
      <div v-if="total > 0" style="display: flex; justify-content: flex-end; margin-top: 16px;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchDocuments"
          @size-change="fetchDocuments"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Delete } from '@element-plus/icons-vue'
import { listDocumentsApi, deleteDocumentApi, type AdminDocumentItem } from '@/api/admin'
import axios from 'axios'

const loading = ref(false)
const documents = ref<AdminDocumentItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterExt = ref('')

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function extTagType(ext: string): 'success' | 'warning' | 'info' | 'danger' | 'primary' | undefined {
  const map: Record<string, 'success' | 'warning' | 'info' | 'danger' | 'primary'> = { '.docx': 'primary', '.doc': 'warning', '.pdf': 'danger', '.txt': 'info' }
  return map[ext] ?? 'info'
}

async function fetchDocuments() {
  loading.value = true
  try {
    const res = await listDocumentsApi({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      file_ext: filterExt.value || undefined,
    })
    documents.value = res.items
    total.value = res.total
  } catch (e: any) {
    ElMessage.error(e?.message || '加载文档列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchDocuments()
}

async function handleDownload(row: AdminDocumentItem) {
  try {
    const token = localStorage.getItem('access_token')
    const res = await axios.get(`/api/v1/admin/documents/${row.file_id}/download`, {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = row.filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    ElMessage.error('下载失败')
  }
}

async function handleDelete(row: AdminDocumentItem) {
  try {
    await deleteDocumentApi(row.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped lang="scss">
.admin-documents {
  padding: 0;
}
</style>
