# 前端高级动效与渲染增强任务清单

- [x] Task 1: 安装轻量图标依赖
    - 1.1: 在 `frontend` 目录安装 `lucide-react`
    - 1.2: 确认 `package.json` 已新增依赖
    - 1.3: 确认 lock 文件已同步更新
    - 1.4: 不新增 `three`、`react-spring`、particles 类依赖

- [x] Task 2: 替换全局导航和操作图标
    - 2.1: 修改 `frontend/src/components/Layout.tsx` 引入 lucide 图标
    - 2.2: 将底部 Tab 的 emoji 替换为 Icon 组件
    - 2.3: 将顶部通知和设置 emoji 替换为 Icon 组件
    - 2.4: 移除通知角标 inline style，改为 CSS class
    - 2.5: 保持通知 SSE 和未读数量逻辑不变

- [x] Task 3: 优化 Layout 图标与导航样式
    - 3.1: 修改 `frontend/src/components/Layout.css` 的 `.icon-btn` 样式
    - 3.2: 修改 `.tab-icon` 适配 SVG 图标
    - 3.3: 增加 active Tab 的微光、颜色和轻微上浮效果
    - 3.4: 新增通知角标 class 样式
    - 3.5: 保持移动端 430px 壳子与底部导航结构不变

- [x] Task 4: 增强全局加载态和恢复档案态
    - 4.1: 修改 `frontend/src/App.tsx` 新增内部 `TasteLoading` 组件
    - 4.2: 将 `PageFallback()` 替换为 `TasteLoading`
    - 4.3: 将 `ProtectedLayout` 的 checking 状态替换为 `TasteLoading`
    - 4.4: 修改 `frontend/src/App.css` 增加信号点、光环和文案样式
    - 4.5: 保持 session 校验和路由跳转逻辑不变

- [x] Task 5: 为首页增加 framer-motion 页面级微动效
    - 5.1: 修改 `frontend/src/pages/Home.tsx` 引入 `motion` 和 `AnimatePresence`
    - 5.2: 为 `today-hero` 增加轻量入场动画
    - 5.3: 为 `signal-card` 增加延迟入场动画
    - 5.4: 为推荐分组增加 stagger 入场动画
    - 5.5: 为快捷操作反馈增加淡入淡出动画
    - 5.6: 不改变首页 API 请求、上传识别和手动补录逻辑

- [x] Task 6: 为首页增加高级 CSS 感知氛围层
    - 6.1: 修改 `frontend/src/pages/Home.tsx` 在首页顶部增加氛围层 DOM
    - 6.2: 修改 `frontend/src/pages/Home.css` 增加味觉信号光环样式
    - 6.3: 使用 transform、opacity、filter 实现低成本动画
    - 6.4: 确保动态背景不遮挡文字和按钮点击
    - 6.5: 控制动画幅度，避免炫技和视觉噪音

- [x] Task 7: 执行构建和回归验证
    - 7.1: 执行 `npm run build`
    - 7.2: 验证 TypeScript 编译通过
    - 7.3: 验证 Vite 生产构建通过
    - 7.4: 检查输出 chunk，确认未引入重型 3D 或粒子依赖
    - 7.5: 检查首页、导航、加载态相关文件无明显运行时风险

- [x] Task 8: 复查并生成总结
    - 8.1: 复查没有修改后端业务逻辑和 AI key fallback
    - 8.2: 复查没有新增 `three`、`react-spring`、particles 类依赖
    - 8.3: 记录实际修改文件、构建结果和视觉收益
    - 8.4: 生成 `.comate/specs/premium-motion-rendering/summary.md`
