<template>
  <div class="admin-users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">用户管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true"><el-icon><Plus /></el-icon>创建用户</el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索工号/姓名" clearable style="width: 200px;" @input="fetchList" />
        <el-select v-model="filterActive" placeholder="全部状态" clearable style="width: 120px;" @change="fetchList">
          <el-option label="全部" value="" />
          <el-option label="启用" value="true" />
          <el-option label="禁用" value="false" />
        </el-select>
      </div>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="employee_id" label="工号" width="120" />
        <el-table-column prop="username" label="姓名" width="120" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column prop="role_name" label="角色" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.role_name || '无' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="handleToggleActive(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="daily_quota" label="日配额" width="80" align="center" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #999;">{{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editUser(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchList" />
      </div>
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingUser ? '编辑用户' : '创建用户'" width="500px" @close="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="工号" required>
          <el-input v-model="form.employee_id" :disabled="!!editingUser" placeholder="工号" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.username" placeholder="姓名" />
        </el-form-item>
        <el-form-item label="密码" :required="!editingUser">
          <el-input v-model="form.password" type="password" :placeholder="editingUser ? '留空不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role_id" placeholder="选择角色" style="width: 100%;">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="部门" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="日配额">
          <el-input-number v-model="form.daily_quota" :min="0" :max="10000" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listUsersApi, createUserApi, updateUserApi, deleteUserApi, listRolesApi, type AdminUserItem, type RoleItem } from '@/api/admin'

const loading = ref(false)
const saving = ref(false)
const users = ref<AdminUserItem[]>([])
const roles = ref<RoleItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const filterActive = ref('')

const showCreateDialog = ref(false)
const editingUser = ref<AdminUserItem | null>(null)
const form = ref({ employee_id: '', username: '', password: '', role_id: 0, department: '', phone: '', daily_quota: 100, remark: '' })

onMounted(async () => {
  try { roles.value = await listRolesApi() } catch {}
  await fetchList()
})

async function fetchList() {
  loading.value = true
  try {
    const isActive = filterActive.value === 'true' ? true : filterActive.value === 'false' ? false : undefined
    const res = await listUsersApi({ page: page.value, page_size: pageSize, keyword: keyword.value || undefined, is_active: isActive })
    users.value = res.items
    total.value = res.total
  } catch {}
  loading.value = false
}

function editUser(row: AdminUserItem) {
  editingUser.value = row
  form.value = { employee_id: row.employee_id, username: row.username, password: '', role_id: row.role_id || 0, department: row.department || '', phone: row.phone || '', daily_quota: row.daily_quota || 100, remark: row.remark || '' }
  showCreateDialog.value = true
}

function resetForm() {
  editingUser.value = null
  form.value = { employee_id: '', username: '', password: '', role_id: 0, department: '', phone: '', daily_quota: 100, remark: '' }
}

async function handleSave() {
  if (!form.value.employee_id || !form.value.username || !form.value.role_id) return ElMessage.warning('请填写必填项')
  if (!editingUser.value && !form.value.password) return ElMessage.warning('请设置密码')
  saving.value = true
  try {
    if (editingUser.value) {
      const data: Record<string, any> = { username: form.value.username, role_id: form.value.role_id, department: form.value.department, phone: form.value.phone, daily_quota: form.value.daily_quota, remark: form.value.remark }
      await updateUserApi(editingUser.value.id, data)
      ElMessage.success('用户已更新')
    } else {
      await createUserApi(form.value as any)
      ElMessage.success('用户已创建')
    }
    showCreateDialog.value = false
    resetForm()
    await fetchList()
  } catch {}
  saving.value = false
}

async function handleToggleActive(row: AdminUserItem) {
  try { await updateUserApi(row.id, { is_active: row.is_active }) } catch { row.is_active = !row.is_active }
}

async function handleDelete(id: number) {
  try { await deleteUserApi(id); ElMessage.success('已删除'); await fetchList() } catch {}
}
</script>

<style scoped lang="scss">
.card-header { display: flex; align-items: center; justify-content: space-between; .card-title { font-size: 18px; font-weight: 600; } }
.filter-bar { display: flex; gap: 8px; margin-bottom: 12px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
