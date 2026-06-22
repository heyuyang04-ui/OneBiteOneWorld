# 修复提醒页返回导航任务清单

- [x] Task 1: 为提醒页增加明确返回入口
    - 1.1: 在 `Notifications.tsx` 中引入 `useNavigate`
    - 1.2: 新增 `handleBack`，优先返回上一页，无历史时回到 `/home`
    - 1.3: 将提醒页标题区改为带“返回”和“回首页”的页面头部
    - 1.4: 保留现有通知列表、空状态和标记已读逻辑

- [x] Task 2: 执行前端构建验证
    - 2.1: 执行 `npm run build`
    - 2.2: 如构建失败，定位并修复 TypeScript 或 Vite 阻断问题
