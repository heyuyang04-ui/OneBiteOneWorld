# meal-photo-description-recognition 任务计划

- [x] Task 1: 扩展后端上传数据结构
    - 1.1: 在 `backend/models/schemas.py` 的 `MealUpload` 中增加可选 `description` 字段
    - 1.2: 在 `backend/routers/meals.py` 中增加用户描述清洗函数
    - 1.3: 将描述限制为 200 字以内
    - 1.4: 保持只传 `image` 的旧上传请求兼容

- [x] Task 2: 将用户描述传入视觉识别链路
    - 2.1: 在 `upload_meal()` 中读取并清洗 `body.description`
    - 2.2: 调用 `vision_skill` 时传入 `description`
    - 2.3: 将 `user_description` 附加到 recognition 与 meal payload
    - 2.4: 确保描述不影响图片大小、类型与 base64 校验

- [x] Task 3: 修改视觉模型 prompt 支持图文联合识别
    - 3.1: 在 `backend/skills/vision_skill.py` 中读取 `description`
    - 3.2: 将用户描述写入 prompt，并要求模型同时参考图片与描述
    - 3.3: 在返回 JSON 要求中增加 `description_used`
    - 3.4: 在异常 fallback 中保留 `description_used` 字段

- [x] Task 4: 在首页上传区增加食物描述输入
    - 4.1: 在 `frontend/src/pages/Home.tsx` 中增加 `foodDescription` 状态
    - 4.2: 在“记录这一餐”区域增加 textarea 输入框
    - 4.3: 提交 `/meals` 时同时发送 `{ image, description }`
    - 4.4: 上传失败时保留描述，方便用户修改后重试

- [x] Task 5: 增加前端样式与交互文案
    - 5.1: 在 `Home.css` 中增加描述输入框样式
    - 5.2: 使用符合当前夜色/木质/琥珀主题的颜色
    - 5.3: 增加 200 字限制提示或 placeholder
    - 5.4: 确保输入框在移动宽度下展示稳定

- [x] Task 6: 运行验证并生成总结
    - 6.1: 执行后端 Python 编译检查
    - 6.2: 执行前端构建检查
    - 6.3: 验证只传 image 的旧流程仍兼容
    - 6.4: 验证 image + description 请求不会 422
    - 6.5: 写入 `.comate/specs/meal-photo-description-recognition/summary.md`
