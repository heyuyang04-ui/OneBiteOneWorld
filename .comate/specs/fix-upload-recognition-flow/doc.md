# fix-upload-recognition-flow 需求说明

## 背景

用户反馈上传图片后识别失败。实际排查发现有两层问题：

1. 浏览器上传前会发送 `OPTIONS /api/meals` CORS 预检，但后端鉴权中间件把所有非公开 `/api/*` 请求都拦截为 401，导致真实 `POST /api/meals` 没有发出。
2. 放行预检后，请求进入后端，但视觉 AI 接口返回 400。当前 `AIClient.vision()` 无论真实图片类型是什么，都固定拼接 `data:image/jpeg;base64,...`，当上传 PNG/WebP 或模型对当前格式敏感时容易触发 400。
3. 当前 `Home.tsx` 对后端返回 `is_food=false` 或 `success=false` 没有明确处理，可能访问 `res.data.data.meal.id` 导致前端误报“识别失败”。

## 修复目标

- 确保所有 CORS `OPTIONS` 预检请求都交给 CORS 中间件处理，不被业务鉴权拦截。
- 后端识别图片时根据 magic number 得到的真实图片类型生成正确 data URL MIME。
- 视觉 AI 调用失败时不要抛出 500，而是返回可控的“识别失败/未识别到食物”结构。
- 前端上传页区分：非食物、后端错误、网络异常，给出明确提示，避免访问不存在的 `meal.id`。

## 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
  - `user_middleware()` 中对 `OPTIONS` 直接 `call_next`。

- `/Users/libowen/Desktop/one-bite-one-world/backend/services/__init__.py`
  - `AIClient.vision()` 支持传入 MIME 类型，生成正确 data URL。
  - 捕获/上抛错误由上层 skill 控制。

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`
  - 从 params 读取 `mime_type`。
  - 捕获视觉模型 HTTP/解析异常，返回 `is_food=false` 和明确 message，避免接口 500。

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - `_validate_image()` 返回图片 bytes、扩展名、MIME 类型。
  - 调用 `vision_skill` 时传入 `mime_type`。
  - `is_food=false` 时保留后端 message。

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
  - 对 `success=false`、`is_food=false`、缺少 `meal.id` 分别处理并 alert 明确信息。

## 边界条件

- JPEG/PNG/WebP 都应通过服务端校验并以正确 MIME 发给视觉模型。
- 非图片、超大图片继续被服务端拒绝。
- AI 服务 400/超时不应导致 `/api/meals` 返回 500。
- 如果模型判断不是食物，前端提示“未识别到食物”，不跳转详情页。

## 验证方案

- 后端编译检查：`python3 -m py_compile backend/main.py backend/services/__init__.py backend/skills/vision_skill.py backend/routers/meals.py`
- 前端构建：`npm run build`
- API 验证：
  - `OPTIONS /api/meals` 返回 200。
  - 带有效 session 上传 PNG/JPEG/WebP 不因 MIME 固定错误触发 500。
  - AI 返回错误时 `/api/meals` 返回 `success=true, data.is_food=false` 或 `success=false`，而不是 500。
