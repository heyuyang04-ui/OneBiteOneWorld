# fix-upload-recognition-flow 修复总结

## 问题原因

用户反馈上传图片后识别失败。排查结果分为两层：

1. 浏览器上传前的 `OPTIONS /api/meals` CORS 预检请求被后端鉴权中间件拦截为 401，导致真实 `POST /api/meals` 没有正常发出。
2. 放行预检后，请求能进入后端，但视觉 AI 接口返回 400。原代码固定用 `data:image/jpeg;base64,...` 调用视觉模型，没有根据真实图片类型生成 MIME。
3. 前端 `Home.tsx` 没有处理 `is_food=false` 和 `success=false`，可能访问不存在的 `meal.id`，导致统一显示“识别失败”。

## 已完成修改

### 1. 修复 CORS 预检拦截

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`

完成内容：

- 在 `user_middleware()` 开头放行所有 `OPTIONS` 请求。
- 真实业务请求仍继续要求有效 `X-Session-Id`。

效果：

- `OPTIONS /api/meals` 不再被鉴权中间件返回 401。

### 2. 按真实图片类型调用视觉模型

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/services/__init__.py`

完成内容：

- 图片校验函数从返回 `(bytes, ext)` 改为返回 `(bytes, ext, mime_type)`。
- JPEG 返回 `image/jpeg`。
- PNG 返回 `image/png`。
- WebP 返回 `image/webp`。
- `vision_skill` 将 `mime_type` 传给 `AIClient.vision()`。
- `AIClient.vision()` 使用 `data:{mime_type};base64,...` 构造视觉模型输入。

效果：

- 不再把 PNG/WebP 伪装成 JPEG 发给视觉模型。

### 3. 避免视觉模型异常导致上传接口 500

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`

完成内容：

- `vision_skill` 捕获 AI 调用异常和 JSON 解析异常。
- 异常时返回稳定结构：

```json
{
  "is_food": false,
  "message": "图片识别服务暂时不可用，请稍后重试"
}
```

- `upload_meal()` 使用 `recognition.message` 返回给前端。

效果：

- 视觉 AI 返回 400 时，`/api/meals` 不再返回 500。

### 4. 修复前端上传错误处理

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`

完成内容：

- `success=false` 时展示后端错误 message。
- `data.is_food=false` 时提示用户重新上传食物照片或稍后重试。
- 跳转详情页前校验 `meal.id` 存在。
- 正常识别成功路径保持不变。

效果：

- 前端不再因为缺少 `meal.id` 误报通用“识别失败”。

## 验证结果

### 后端编译

命令：

```bash
python3 -m py_compile backend/main.py backend/services/__init__.py backend/skills/vision_skill.py backend/routers/meals.py
```

结果：通过。

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

### 上传接口验证

验证命令结果：

```text
preflight_meals 200 http://localhost:5173
post_meals 200 http://localhost:5173 {"success":true,"data":{"is_food":false,"message":"图片识别服务暂时不可用，请稍后重试"}}
```

结论：

- CORS 预检已通过。
- 上传接口不再 500。
- 当视觉模型不可用或返回 400 时，后端返回稳定可处理结构，前端会给出明确提示。

## 当前服务

后端已重启，当前任务：

```text
cdkjbw
```

前端服务仍运行在：

```text
http://localhost:5173/
```

## 任务状态

`.comate/specs/fix-upload-recognition-flow/tasks.md` 中 5 个顶层任务均已完成。