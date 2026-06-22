# fixpoint.txt 问题批量修复总结

## 修复概览

已根据 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt` 完成本轮可安全落地的问题修复。城市区县死链问题在上一轮 `fix-city-module-rendering` 中已修复，本轮继续处理通知、餐食图片、餐食渲染、匹配数据、城市接口隐患和前端健壮性问题。

硬编码 AI API Key 项未修改，原因：当前项目已有明确约束要求保留 `backend/config.py` 中的硬编码 API key fallback，且安全 skill 当前不开放硬编码凭证自动修复流程。

## 已完成内容

### 1. SSE 通知用户识别
修改文件：
- `frontend/src/components/Layout.tsx`
- `backend/routers/notifications.py`

完成内容：
- 前端使用 `URLSearchParams` 拼接 EventSource query，移除 `?&x_user_id=...` 形式。
- 后端 SSE 端点支持 `x_session_id` 和 `x_user_id` query 参数。
- 解析优先级：有效 session > query user_id > `request.state.user_id`。
- 修复切换用户后铃铛未读数仍按 `user_01` 统计的问题。

### 2. 餐食图片展示与列表 payload 优化
修改文件：
- `backend/routers/meals.py`
- `frontend/src/pages/MealResult.tsx`
- `frontend/src/pages/MealResult.css`
- `frontend/src/pages/MealHistory.tsx`

完成内容：
- 新增 nutrition 数字清洗 helper。
- 上传落库前清洗 nutrition 字段。
- `list_meals` 不再内联返回图片 base64，只返回 `has_image`。
- 新增 `/api/meals/{meal_id}/image` 按需获取图片。
- 餐食详情页展示上传图片。
- 历史记录页按需拉取并展示缩略图。

### 3. 餐食结果口味与营养渲染异常
修改文件：
- `frontend/src/pages/MealResult.tsx`

完成内容：
- 过滤 0 或极小值口味维度，避免空进度条。
- 无突出维度时展示弱提示。
- 营养字段展示时做数字提取兜底，避免 `350kcal千卡` 这类重复单位。

### 4. 匹配重复写入、pending 方向和 private 越权点赞
修改文件：
- `backend/routers/match.py`
- `frontend/src/pages/MatchList.tsx`

完成内容：
- like 前校验对方用户存在。
- private 用户拒绝被直接构造请求点赞。
- 写入 pending 前检查同方向 pending/mutual 是否已存在。
- 已存在记录时返回已有状态，不重复插入。
- `/match/list` 返回 `direction` 字段。
- pending 列表展示“待你确认 / 等待对方回应”。

### 5. 城市接口隐患清理
修改文件：
- `backend/routers/city.py`

完成内容：
- 删除 heatmap 接口中未使用的 `trend_skill` 调用。
- 修复 get_district 找到区县后只跳出内层循环的问题。
- district 返回数据补充 `city` 和 `city_name`。

### 6. 登录无效请求与发现页点赞失败处理
修改文件：
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/SocialDiscover.tsx`

完成内容：
- 删除 Login 中无意义的 `/users` 请求。
- 保留固定体验用户入口和 Bowen 用户。
- 同步体验用户展示名为更真实姓名。
- 发现页 like 成功后再切换下一张。
- like 失败时提示用户，并保留当前卡片。
- 增加 actionLoading 防止重复点击并发请求。

## 验证结果

### 前端构建
已运行：

```bash
npm run build
```

结果：成功。

```text
✓ 1117 modules transformed.
✓ built in 435ms
```

Vite 仅提示 bundle 大小超过 500kB，这是体积提示，不影响运行。

### 后端语法检查
已运行：

```bash
python -m py_compile routers/notifications.py routers/meals.py routers/match.py routers/city.py
```

结果：成功，无语法错误。

### 接口 smoke test
当前 8000 后端实例返回正常：

- `/api/notifications`：200 success=true
- `/api/meals?limit=1`：200 success=true
- `/api/match/list?status=pending`：200 success=true
- `/api/city/heatmap?city=beijing&dimension=spicy`：200 success=true

### 主题残留检查
前端源码旧紫色/旧主题硬编码检查：未检出。

## 未处理项说明

- #1 城市区县死链：已在上一轮城市模块修复中完成。
- #12 SESSION/JWT 鉴权架构：属于正式鉴权体系改造，本轮不做大改。
- #14 硬编码 AI API Key：按当前项目约束保留，不修改。
- #15 统一错误响应规范：涉及全局接口契约，本轮不做。
- #16 上传图片服务端类型/大小校验：安全增强项，可后续单独处理。
- #18 WeeklyReport 打字机性能：非用户主路径 bug，本轮不改。
- #19 全局 catch 静默吞错：全局体验改造，本轮不做全量改动。
- #20 城市地图真实 geo：需要引入地图数据或 geoJSON，超出本轮 bug 修复范围。
