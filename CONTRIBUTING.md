# 贡献指南

感谢你对 TextGuard 的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

- 在 Issues 中搜索是否已有类似问题
- 使用 Bug Report 模板创建新 Issue
- 提供复现步骤、预期行为和实际行为

### 提交功能建议

- 在 Issues 中描述你的需求场景
- 说明期望的功能表现
- 如果可能，提供设计思路

### 提交代码

1. Fork 项目到你的仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码并确保通过测试
4. 提交变更：`git commit -m 'feat: add your feature'`
5. 推送分支：`git push origin feature/your-feature`
6. 创建 Pull Request

### Commit 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `style:` 代码格式（不影响逻辑）
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具变更

## 开发环境

请参考 [README.md](README.md) 中的「快速开始」章节搭建本地开发环境。

## 代码规范

- **后端**：遵循 PEP 8，使用 Type Hints
- **前端**：使用 TypeScript，遵循 Vue 3 Composition API 风格
- **注释**：关键逻辑添加中文注释

## 协议

参与贡献即表示你同意你的代码遵循项目的 [MIT License](LICENSE)。
