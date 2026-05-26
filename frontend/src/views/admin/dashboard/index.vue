<template>
  <div class="admin-dashboard">
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #ecf5ff;"><el-icon :size="28" color="#409eff"><Edit /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.today_proofread_count }}</div>
            <div class="stat-label">今日校对次数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #f0f9eb;"><el-icon :size="28" color="#67c23a"><Document /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_proofread_count }}</div>
            <div class="stat-label">累计校对次数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #fdf6ec;"><el-icon :size="28" color="#e6a23c"><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #fef0f0;"><el-icon :size="28" color="#f56c6c"><UserFilled /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.active_users_today }}</div>
            <div class="stat-label">今日活跃用户</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #f3e8ff;"><el-icon :size="28" color="#7c3aed"><Folder /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.today_document_count }} / {{ stats.total_document_count }}</div>
            <div class="stat-label">今日/累计上传文档</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #e0f2fe;"><el-icon :size="28" color="#0284c7"><Coin /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ formatTokens(stats.total_token_usage) }}</div>
            <div class="stat-label">累计 Token 消耗</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">系统信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="平台名称">{{ siteStore.platformName }} {{ siteStore.platformSubtitle }}</el-descriptions-item>
        <el-descriptions-item label="后端框架">FastAPI + SQLAlchemy</el-descriptions-item>
        <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
        <el-descriptions-item label="AI 模型">DeepSeek</el-descriptions-item>
        <el-descriptions-item label="数据库">PostgreSQL</el-descriptions-item>
        <el-descriptions-item label="缓存">Redis</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getDashboardStatsApi, type DashboardStats } from '@/api/admin'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()

const stats = reactive<DashboardStats>({
  today_proofread_count: 0,
  total_proofread_count: 0,
  total_users: 0,
  active_users_today: 0,
  total_token_usage: 0,
  today_document_count: 0,
  total_document_count: 0,
})

function formatTokens(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

onMounted(async () => {
  try {
    const data = await getDashboardStatsApi()
    Object.assign(stats, data)
  } catch {}
})
</script>

<style scoped lang="scss">
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}
.stat-card {
  .stat-content { display: flex; align-items: center; gap: 16px; }
  .stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
  .stat-info {
    .stat-value { font-size: 28px; font-weight: 700; color: #333; line-height: 1.2; }
    .stat-label { font-size: 13px; color: #999; margin-top: 4px; }
  }
}
</style>
