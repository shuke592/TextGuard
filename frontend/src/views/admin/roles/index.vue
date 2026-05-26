<template>
  <div class="admin-roles">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">角色权限管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true"><el-icon><Plus /></el-icon>新建角色</el-button>
        </div>
      </template>

      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="code" label="角色编码" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'danger' : 'info'" size="small">{{ row.is_system ? '系统' : '自定义' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限数" width="80" align="center">
          <template #default="{ row }">{{ row.permission_ids?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editRole(row)" :disabled="row.code === 'super_admin'">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small" :disabled="row.is_system">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingRole ? '编辑角色' : '新建角色'" width="600px" @close="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="角色名称" />
        </el-form-item>
        <el-form-item label="编码" required v-if="!editingRole">
          <el-input v-model="form.code" placeholder="角色编码（如 editor）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="描述" />
        </el-form-item>
        <el-form-item label="权限">
          <el-tree
            ref="treeRef"
            :data="permissionTree"
            :props="{ label: 'name', children: 'children' }"
            show-checkbox
            node-key="id"
            :default-checked-keys="form.permission_ids"
            style="width: 100%;"
          />
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
import { listRolesApi, createRoleApi, updateRoleApi, deleteRoleApi, getPermissionTreeApi, type RoleItem, type PermissionItem } from '@/api/admin'

const loading = ref(false)
const saving = ref(false)
const roles = ref<RoleItem[]>([])
const permissionTree = ref<PermissionItem[]>([])
const treeRef = ref<any>(null)

const showCreateDialog = ref(false)
const editingRole = ref<RoleItem | null>(null)
const form = ref({ name: '', code: '', description: '', permission_ids: [] as number[] })

onMounted(async () => {
  try { permissionTree.value = await getPermissionTreeApi() } catch {}
  await fetchList()
})

async function fetchList() {
  loading.value = true
  try { roles.value = await listRolesApi() } catch {}
  loading.value = false
}

function editRole(row: RoleItem) {
  editingRole.value = row
  form.value = { name: row.name, code: row.code, description: row.description || '', permission_ids: [...row.permission_ids] }
  showCreateDialog.value = true
}

function resetForm() {
  editingRole.value = null
  form.value = { name: '', code: '', description: '', permission_ids: [] }
}

async function handleSave() {
  if (!form.value.name) return ElMessage.warning('请填写角色名称')
  const checkedIds = treeRef.value?.getCheckedKeys() || []
  saving.value = true
  try {
    if (editingRole.value) {
      await updateRoleApi(editingRole.value.id, { name: form.value.name, description: form.value.description, permission_ids: checkedIds })
      ElMessage.success('角色已更新')
    } else {
      if (!form.value.code) return ElMessage.warning('请填写角色编码')
      await createRoleApi({ name: form.value.name, code: form.value.code, description: form.value.description, permission_ids: checkedIds })
      ElMessage.success('角色已创建')
    }
    showCreateDialog.value = false
    resetForm()
    await fetchList()
  } catch {}
  saving.value = false
}

async function handleDelete(id: number) {
  try { await deleteRoleApi(id); ElMessage.success('已删除'); await fetchList() } catch {}
}
</script>

<style scoped lang="scss">
.card-header { display: flex; align-items: center; justify-content: space-between; .card-title { font-size: 18px; font-weight: 600; } }
</style>
