<template>
  <div class="admin-policy">
    <el-card>
      <template #header><span style="font-weight: 600;">游客策略</span></template>
      <el-form label-width="160px" style="max-width: 500px;">
        <el-form-item label="每日校对次数上限">
          <el-input-number v-model="guestPolicy.daily_limit" :min="0" :max="1000" />
        </el-form-item>
        <el-form-item label="单次最大字数">
          <el-input-number v-model="guestPolicy.max_text_length" :min="100" :max="100000" :step="1000" />
        </el-form-item>
        <el-form-item label="允许上传文档">
          <el-switch v-model="guestPolicy.allow_upload" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveGuestPolicy">保存游客策略</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">登录用户默认策略</span></template>
      <el-form label-width="160px" style="max-width: 500px;">
        <el-form-item label="每日校对次数上限">
          <el-input-number v-model="userPolicy.daily_limit" :min="0" :max="100000" />
        </el-form-item>
        <el-form-item label="单次最大字数">
          <el-input-number v-model="userPolicy.max_text_length" :min="100" :max="500000" :step="5000" />
        </el-form-item>
        <el-form-item label="允许上传文档">
          <el-switch v-model="userPolicy.allow_upload" />
        </el-form-item>
        <el-form-item label="允许导出报告">
          <el-switch v-model="userPolicy.allow_export" />
        </el-form-item>
        <el-form-item label="允许个性化词库">
          <el-switch v-model="userPolicy.allow_dictionary" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveUserPolicy">保存用户策略</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  type GuestPolicyConfig, type UserPolicyConfig,
  getGuestPolicyApi, updateGuestPolicyApi,
  getUserPolicyApi, updateUserPolicyApi,
} from '@/api/admin'

const guestPolicy = reactive<GuestPolicyConfig>({
  daily_limit: 20,
  max_text_length: 5000,
  allow_upload: true,
})

const userPolicy = reactive<UserPolicyConfig>({
  daily_limit: 200,
  max_text_length: 50000,
  allow_upload: true,
  allow_export: true,
  allow_dictionary: true,
})

onMounted(async () => {
  try {
    const guest = await getGuestPolicyApi()
    Object.assign(guestPolicy, guest)
  } catch {}
  
  try {
    const user = await getUserPolicyApi()
    Object.assign(userPolicy, user)
  } catch {}
})

async function saveGuestPolicy() {
  try {
    await updateGuestPolicyApi(guestPolicy)
    ElMessage.success('游客策略已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function saveUserPolicy() {
  try {
    await updateUserPolicyApi(userPolicy)
    ElMessage.success('用户策略已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}
</script>

<style scoped lang="scss">
</style>
