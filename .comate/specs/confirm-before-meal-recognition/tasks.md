# confirm-before-meal-recognition 任务计划

- [x] Task 1: 调整 ImageUpload 为只选择图片不自动识别
    - 1.1: 将 props 从 `onUpload` 改为 `onImageReady`
    - 1.2: 选择图片后只设置 preview 并回传 base64
    - 1.3: 移除选择图片后立即触发识别的行为
    - 1.4: 保留 resetKey 清空 preview 的逻辑

- [x] Task 2: 拆分 Home 的图片选择与确认识别流程
    - 2.1: 在 `Home.tsx` 中增加 `pendingImage` 状态
    - 2.2: 新增 `handleImageReady` 只保存 base64
    - 2.3: 将原 `handleUpload` 改为 `handleConfirmRecognition`
    - 2.4: 提交时使用 `pendingImage + foodDescription`

- [x] Task 3: 增加确认识别按钮与状态控制
    - 3.1: 在上传区增加“确认识别这一餐”按钮
    - 3.2: 未选择图片时禁用按钮并提示先选择照片
    - 3.3: loading 时禁用按钮并显示识别中状态
    - 3.4: 失败时清空 pendingImage 和图片预览，但保留描述

- [x] Task 4: 增加确认按钮样式
    - 4.1: 在 `Home.css` 中增加 `.recognition-actions` 样式
    - 4.2: 增加 `.confirm-recognition-btn` 样式
    - 4.3: 增加 disabled 状态样式
    - 4.4: 保持当前夜色/木质/琥珀主题一致

- [x] Task 5: 运行验证并生成总结
    - 5.1: 执行前端构建检查
    - 5.2: 静态确认 `ImageUpload` 不再调用 `/meals`
    - 5.3: 静态确认 `/meals` 只在确认按钮流程中调用
    - 5.4: 写入 `.comate/specs/confirm-before-meal-recognition/summary.md`
