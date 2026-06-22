# fixpoint-followup-hardening 增量修复任务计划

- [x] Task 1: 为 matches 增加数据库级唯一约束兜底
    - 1.1: 在 `backend/database.py` 中新增 matches 去重迁移函数
    - 1.2: 在数据库初始化流程中调用去重与唯一索引创建逻辑
    - 1.3: 确保唯一索引使用 `(user_a, user_b)` 有向关系，不破坏 mutual 匹配模型
    - 1.4: 验证已有重复数据不会阻止索引创建

- [x] Task 2: 修复上传成功后 MealResult 首屏不显示照片
    - 2.1: 在 `frontend/src/pages/MealResult.tsx` 中检测 `meal.id` 存在但 `meal.image` 缺失的状态
    - 2.2: 调用 `GET /meals/{id}/image` 补拉 base64 图片
    - 2.3: 将返回的图片合并进当前 meal state
    - 2.4: 确保图片补拉失败不影响餐食详情主体渲染

- [x] Task 3: 增加上传图片服务端大小与类型校验
    - 3.1: 在 `backend/routers/meals.py` 中新增 base64 严格解码工具
    - 3.2: 增加 5MB 服务端大小上限校验
    - 3.3: 使用 magic number 校验 JPEG、PNG、WebP 真实图片类型
    - 3.4: 在调用视觉识别与写盘前执行校验，校验失败时返回明确错误
    - 3.5: 根据真实图片类型保存对应扩展名文件

- [x] Task 4: 运行验证并生成本轮修复总结
    - 4.1: 执行 Python 编译检查验证后端语法
    - 4.2: 执行前端构建验证 TypeScript/React 编译
    - 4.3: 验证数据库唯一索引创建逻辑
    - 4.4: 写入 `.comate/specs/fixpoint-followup-hardening/summary.md`
