<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- 用户头像区域 -->
      <el-card class="avatar-card">
        <div class="avatar-section">
          <el-avatar :size="80" :src="userInfo?.avatar || defaultAvatar" />
          <div class="avatar-info">
            <h3 class="user-name">{{ userInfo?.username }}</h3>
            <p class="user-dept">{{ userInfo?.department || '未设置部门' }}</p>
            <p class="user-role">
              <el-tag size="small" type="primary">{{ userInfo?.role_name || '普通用户' }}</el-tag>
            </p>
          </div>
        </div>
        <div class="user-meta">
          <div class="meta-item">
            <span class="meta-label">工号</span>
            <span class="meta-value">{{ userInfo?.employee_id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">登录方式</span>
            <span class="meta-value">
              <el-tag v-if="feishuBound" size="small" type="success">飞书已绑定</el-tag>
              <el-tag v-else size="small" type="info">账号密码</el-tag>
            </span>
          </div>
        </div>
      </el-card>

      <!-- 基本信息编辑 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button v-if="!editMode" text type="primary" @click="editMode = true">编辑</el-button>
            <div v-else>
              <el-button text @click="cancelEdit">取消</el-button>
              <el-button type="primary" text :loading="saving" @click="saveProfile">保存</el-button>
            </div>
          </div>
        </template>
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="80px"
          :disabled="!editMode"
        >
          <el-form-item label="姓名" prop="username">
            <el-input v-model="profileForm.username" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="性别" prop="gender">
            <el-radio-group v-model="profileForm.gender">
              <el-radio value="male">男</el-radio>
              <el-radio value="female">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="工号">
            <el-input :model-value="userInfo?.employee_id" disabled />
            <div class="form-tip">工号不可修改</div>
          </el-form-item>
          <el-form-item label="部门">
            <el-input :model-value="userInfo?.department || '未分配'" disabled />
            <div class="form-tip">部门由管理员分配</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码 -->
      <el-card class="password-card">
        <template #header><span>修改密码</span></template>
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
        >
          <el-form-item label="当前密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码（至少6位）"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="changingPwd" @click="handleChangePassword">
              确认修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, FormInstance } from 'element-plus'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const defaultAvatar = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"%3E%3Cpath d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/%3E%3C/svg%3E'

// 飞书绑定状态
const feishuBound = computed(() => {
  return false // 后续可通过userInfo扩展判断
})

// 编辑模式
const editMode = ref(false)
const saving = ref(false)
const profileFormRef = ref<FormInstance>()

const profileForm = reactive({
  username: '',
  phone: '',
  gender: '',
})

const profileRules = {
  username: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

// 密码修改
const changingPwd = ref(false)
const passwordFormRef = ref<FormInstance>()

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 初始化表单
function initForm() {
  if (userInfo.value) {
    profileForm.username = userInfo.value.username || ''
    profileForm.phone = userInfo.value.phone || ''
    profileForm.gender = userInfo.value.gender || ''
  }
}

// 取消编辑
function cancelEdit() {
  editMode.value = false
  initForm()
}

// 保存个人信息
async function saveProfile() {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await request.put('/auth/profile', {
        username: profileForm.username,
        phone: profileForm.phone || null,
        gender: profileForm.gender || null,
      })
      ElMessage.success('个人信息修改成功')
      editMode.value = false
      // 刷新用户信息
      await userStore.fetchUserInfo()
    } catch (e) {
      // axios拦截器处理
    } finally {
      saving.value = false
    }
  })
}

// 修改密码
async function handleChangePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    changingPwd.value = true
    try {
      await request.put('/auth/password', {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      })
      ElMessage.success('密码修改成功')
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
    } catch (e) {
      // axios拦截器处理
    } finally {
      changingPwd.value = false
    }
  })
}

onMounted(() => {
  initForm()
})
</script>

<style scoped lang="scss">
.profile-page {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.profile-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 头像区域 */
.avatar-card {
  .avatar-section {
    display: flex;
    align-items: center;
    gap: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f0f0f0;
  }

  .avatar-info {
    .user-name {
      font-size: 20px;
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }
    .user-dept {
      font-size: 14px;
      color: #666;
      margin-bottom: 6px;
    }
  }

  .user-meta {
    display: flex;
    gap: 40px;
    padding-top: 16px;
  }

  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .meta-label {
    font-size: 12px;
    color: #999;
  }

  .meta-value {
    font-size: 14px;
    color: #333;
  }
}

/* 信息编辑卡片 */
.info-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-page {
    padding: 12px;
  }

  .avatar-card .avatar-section {
    flex-direction: column;
    text-align: center;
  }

  .avatar-card .user-meta {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
