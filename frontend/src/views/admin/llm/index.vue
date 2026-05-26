<template>
  <div class="admin-llm">
    <!-- 顶部操作栏 -->
    <div class="top-bar">
      <div>
        <span class="page-title">大模型配置管理</span>
        <el-tag v-if="activeConfig" type="success" size="small" style="margin-left: 12px;">
          当前使用：{{ activeConfig.name }} ({{ activeConfig.model }})
        </el-tag>
      </div>
      <el-button type="primary" @click="openAddDialog"><el-icon><Plus /></el-icon>添加模型</el-button>
    </div>

    <!-- 模型卡片列表 -->
    <div class="config-grid" v-loading="loading">
      <el-card
        v-for="item in configList" :key="item.id"
        :class="['config-card', { 'active-card': item.is_active, 'disabled-card': !item.is_enabled }]"
        shadow="hover"
      >
        <div class="card-top">
          <div class="card-name">
            <span class="name-text">{{ item.name }}</span>
            <el-tag v-if="item.is_active" type="success" size="small" effect="dark">使用中</el-tag>
            <el-tag v-if="!item.is_enabled" type="info" size="small">已停用</el-tag>
          </div>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, item)">
            <el-button :icon="MoreFilled" link />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="test">测试连接</el-dropdown-item>
                <el-dropdown-item v-if="!item.is_active && item.is_enabled" command="activate">设为当前使用</el-dropdown-item>
                <el-dropdown-item v-if="item.is_enabled" command="disable">停用</el-dropdown-item>
                <el-dropdown-item v-if="!item.is_enabled" command="enable">启用</el-dropdown-item>
                <el-dropdown-item v-if="!item.is_active" command="delete" divided style="color: #f56c6c;">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="card-info">
          <div class="info-row">
            <span class="info-label">供应商</span>
            <el-tag size="small" type="info">{{ providerNameMap[item.provider] || item.provider }}</el-tag>
          </div>
          <div class="info-row">
            <span class="info-label">模型</span>
            <span class="info-value model-name">{{ item.model }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">API 地址</span>
            <span class="info-value" style="font-size: 12px; color: #999;">{{ item.api_base }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">密钥</span>
            <span class="info-value" style="font-family: monospace; color: #999;">{{ item.api_key_masked }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">参数</span>
            <span class="info-value" style="font-size: 12px;">
              温度={{ item.temperature }} | 超时={{ item.timeout }}s | 重试={{ item.max_retries }}
            </span>
          </div>
        </div>

        <div class="card-footer">
          <el-button
            v-if="!item.is_active && item.is_enabled"
            type="primary" size="small" plain
            @click="handleActivate(item.id)"
          >设为当前使用</el-button>
          <el-button size="small" plain :loading="testingId === item.id" @click="handleTest(item.id)">
            {{ testingId === item.id ? '测试中...' : '测试连接' }}
          </el-button>
        </div>
      </el-card>

      <el-empty v-if="!loading && configList.length === 0" description="暂无模型配置，请点击添加" />
    </div>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="showFormDialog" :title="editingId ? '编辑模型配置' : '添加模型配置'" width="600px" destroy-on-close>
      <el-form :model="formData" label-width="100px">
        <el-form-item label="供应商" required>
          <el-select v-model="formData.provider" placeholder="选择供应商" style="width: 100%;" @change="onProviderChange">
            <el-option
              v-for="p in providerOptions" :key="p.code"
              :label="p.name" :value="p.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="配置名称" required>
          <el-input v-model="formData.name" placeholder="如：DeepSeek 生产环境、GPT-4o 备用" />
        </el-form-item>
        <el-form-item label="API 地址" required>
          <el-input v-model="formData.api_base" placeholder="https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="formData.api_key" type="password" show-password placeholder="sk-..." />
          <div v-if="editingId" style="font-size: 12px; color: #999; margin-top: 4px;">留空则保持原密钥不变</div>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="formData.model" placeholder="deepseek-chat" />
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="formData.temperature" :min="0" :max="2" :step="0.1" show-input style="width: 100%;" />
        </el-form-item>
        <el-form-item label="最大 Token">
          <el-input-number v-model="formData.max_tokens" :min="0" :max="128000" placeholder="0 表示不限" />
          <span style="margin-left: 8px; font-size: 12px; color: #999;">0 或空表示不限制</span>
        </el-form-item>
        <el-form-item label="超时(秒)">
          <el-input-number v-model="formData.timeout" :min="10" :max="600" />
        </el-form-item>
        <el-form-item label="重试次数">
          <el-input-number v-model="formData.max_retries" :min="0" :max="10" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled } from '@element-plus/icons-vue'
import {
  type LLMConfigItem, type LLMProviderOption,
  listLLMConfigsApi, listLLMProvidersApi,
  createLLMConfigApi, updateLLMConfigApi,
  deleteLLMConfigApi, activateLLMConfigApi, testLLMConfigApi,
} from '@/api/admin'

const loading = ref(false)
const submitting = ref(false)
const testingId = ref<number | null>(null)
const configList = ref<LLMConfigItem[]>([])
const providerOptions = ref<LLMProviderOption[]>([])

const showFormDialog = ref(false)
const editingId = ref<number | null>(null)
const formData = reactive({
  name: '', provider: 'deepseek', api_base: '', api_key: '', model: '',
  temperature: 0.3, max_tokens: 0, timeout: 60, max_retries: 3, remark: '',
})

const activeConfig = computed(() => configList.value.find(c => c.is_active))

const providerNameMap = computed(() => {
  const map: Record<string, string> = {}
  providerOptions.value.forEach(p => { map[p.code] = p.name })
  return map
})

onMounted(() => {
  fetchProviders()
  fetchList()
})

async function fetchProviders() {
  try {
    providerOptions.value = await listLLMProvidersApi()
  } catch (e) { /* 静默 */ }
}

async function fetchList() {
  loading.value = true
  try {
    configList.value = await listLLMConfigsApi()
  } catch (e) {
    ElMessage.error('加载模型配置失败')
  } finally {
    loading.value = false
  }
}

function onProviderChange(code: string) {
  const p = providerOptions.value.find(o => o.code === code)
  if (p) {
    if (!formData.api_base || formData.api_base === '') formData.api_base = p.default_base
    if (!formData.model || formData.model === '') formData.model = p.default_model
    if (!formData.name || formData.name === '') formData.name = p.name
  }
}

function openAddDialog() {
  editingId.value = null
  Object.assign(formData, {
    name: '', provider: 'deepseek', api_base: '', api_key: '', model: '',
    temperature: 0.3, max_tokens: 0, timeout: 60, max_retries: 3, remark: '',
  })
  showFormDialog.value = true
}

function openEditDialog(item: LLMConfigItem) {
  editingId.value = item.id
  Object.assign(formData, {
    name: item.name, provider: item.provider, api_base: item.api_base,
    api_key: item.api_key || '', model: item.model, temperature: item.temperature,
    max_tokens: item.max_tokens || 0, timeout: item.timeout,
    max_retries: item.max_retries, remark: item.remark || '',
  })
  showFormDialog.value = true
}

async function handleSubmit() {
  if (!formData.name.trim()) return ElMessage.warning('请输入配置名称')
  if (!formData.api_base.trim()) return ElMessage.warning('请输入 API 地址')
  if (!editingId.value && !formData.api_key.trim()) return ElMessage.warning('请输入 API Key')
  if (!formData.model.trim()) return ElMessage.warning('请输入模型名称')

  submitting.value = true
  try {
    const payload: any = { ...formData }
    if (payload.max_tokens === 0) payload.max_tokens = null
    // 编辑时如果密钥留空则不提交
    if (editingId.value && !payload.api_key) delete payload.api_key

    if (editingId.value) {
      await updateLLMConfigApi(editingId.value, payload)
      ElMessage.success('配置已更新')
    } else {
      await createLLMConfigApi(payload)
      ElMessage.success('配置已添加')
    }
    showFormDialog.value = false
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleActivate(id: number) {
  try {
    await activateLLMConfigApi(id)
    ElMessage.success('已切换当前使用的模型')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '切换失败')
  }
}

async function handleTest(id: number) {
  testingId.value = id
  try {
    const result = await testLLMConfigApi(id)
    if (result.success) {
      ElMessage.success(`连接成功！模型: ${result.model}，回复: ${result.message}`)
    } else {
      ElMessage.error(`连接失败: ${result.message}`)
    }
  } catch (e: any) {
    ElMessage.error('测试请求失败')
  } finally {
    testingId.value = null
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该模型配置？', '删除确认', { type: 'warning' })
    await deleteLLMConfigApi(id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

async function handleToggleEnabled(item: LLMConfigItem, enabled: boolean) {
  try {
    await updateLLMConfigApi(item.id, { is_enabled: enabled })
    ElMessage.success(enabled ? '已启用' : '已停用')
    fetchList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function handleCommand(cmd: string, item: LLMConfigItem) {
  switch (cmd) {
    case 'edit': openEditDialog(item); break
    case 'test': handleTest(item.id); break
    case 'activate': handleActivate(item.id); break
    case 'disable': handleToggleEnabled(item, false); break
    case 'enable': handleToggleEnabled(item, true); break
    case 'delete': handleDelete(item.id); break
  }
}
</script>

<style scoped lang="scss">
.admin-llm {
  .top-bar {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    .page-title { font-size: 18px; font-weight: 600; color: #333; }
  }

  .config-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 16px;
  }

  .config-card {
    border-radius: 8px;
    transition: all 0.2s;
    &.active-card { border: 2px solid #0056b3; }
    &.disabled-card { opacity: 0.6; }

    .card-top {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;
      .card-name {
        display: flex; align-items: center; gap: 8px;
        .name-text { font-size: 16px; font-weight: 600; color: #333; }
      }
    }

    .card-info {
      .info-row {
        display: flex; align-items: center; padding: 4px 0; gap: 8px;
        .info-label { font-size: 13px; color: #999; min-width: 50px; flex-shrink: 0; }
        .info-value { font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .model-name { font-weight: 600; color: #0056b3; }
      }
    }

    .card-footer {
      display: flex; gap: 8px; margin-top: 16px; padding-top: 12px; border-top: 1px solid #f0f0f0;
    }
  }
}
</style>
