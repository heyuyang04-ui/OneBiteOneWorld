# fix-upload-recognition-flow 修复任务计划

- [x] Task 1: 修复上传接口 CORS 预检被鉴权拦截
    - 1.1: 在 `backend/main.py` 的 `user_middleware` 中放行所有 `OPTIONS` 请求
    - 1.2: 确保真实业务请求仍然要求有效 `X-Session-Id`
    - 1.3: 验证 `OPTIONS /api/meals` 返回 200 而不是 401

- [x] Task 2: 按真实图片类型调用视觉模型
    - 2.1: 修改 `backend/routers/meals.py` 的图片校验函数，返回 MIME 类型
    - 2.2: 将 MIME 类型传入 `vision_skill`
    - 2.3: 修改 `backend/skills/vision_skill.py`，读取并传递 `mime_type`
    - 2.4: 修改 `backend/services/__init__.py` 的 `AIClient.vision`，按 MIME 生成 data URL

- [x] Task 3: 避免视觉模型异常导致上传接口 500
    - 3.1: 在 `vision_skill` 中捕获 AI 调用异常
    - 3.2: AI 调用失败时返回稳定的 `is_food=false` 结构和明确 message
    - 3.3: 保持 JSON 解析失败时也返回稳定结构
    - 3.4: 确保 `/api/meals` 不因视觉 AI 400 直接 500

- [x] Task 4: 修复前端上传错误处理
    - 4.1: 在 `Home.tsx` 中处理 `success=false` 并展示后端错误 message
    - 4.2: 在 `Home.tsx` 中处理 `data.is_food=false`，提示用户重新上传食物照片
    - 4.3: 在跳转前校验 `data.meal.id` 存在
    - 4.4: 保持正常识别成功后进入 `MealResult`

- [x] Task 5: 运行验证并生成总结
    - 5.1: 执行后端 Python 编译检查
    - 5.2: 执行前端构建检查
    - 5.3: 验证上传预检和最小图片上传不再返回 500
    - 5.4: 写入 `.comate/specs/fix-upload-recognition-flow/summary.md`
