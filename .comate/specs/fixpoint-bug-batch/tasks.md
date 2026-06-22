# fixpoint.txt 问题批量修复任务

- [x] Task 1: 修复 SSE 通知用户识别
    - 1.1: 更新 `Layout.tsx`，使用 `URLSearchParams` 拼接 EventSource 参数
    - 1.2: 更新 `notifications.py`，在 SSE 端点中解析 `x_session_id` 和 `x_user_id` query 参数
    - 1.3: 优先使用有效 session，其次使用 query user_id，最后回退 `request.state.user_id`
    - 1.4: 保持普通通知列表接口不变

- [x] Task 2: 修复餐食图片展示与列表 payload 过大问题
    - 2.1: 更新 `meals.py`，新增 nutrition 数字清洗 helper
    - 2.2: 上传落库前清洗 nutrition 字段，避免重复单位展示
    - 2.3: 修改 `list_meals`，不再内联返回图片 base64，仅返回轻量图片状态
    - 2.4: 新增 `/api/meals/{meal_id}/image` 按需获取图片接口
    - 2.5: 更新 `MealResult.tsx` 和 `MealResult.css`，展示详情图片
    - 2.6: 更新 `MealHistory.tsx`，按需加载并展示历史缩略图

- [x] Task 3: 修复餐食结果口味与营养渲染异常
    - 3.1: 在 `MealResult.tsx` 中过滤 0 或极小值口味维度
    - 3.2: 当无有效口味维度时展示弱提示文案
    - 3.3: 前端展示 nutrition 时做数字兜底
    - 3.4: 保持下一餐建议和味觉画像影响逻辑不变

- [x] Task 4: 修复匹配重复写入、pending 方向和 private 越权点赞
    - 4.1: 更新 `match.py`，like 前校验对方用户存在且不是 private
    - 4.2: 写入 pending 前检查同方向是否已有 pending/mutual 记录
    - 4.3: 已存在记录时返回已有状态，不重复插入
    - 4.4: 更新 `match_list` 返回 `direction` 字段
    - 4.5: 更新 `MatchList.tsx` 展示 pending 方向提示

- [x] Task 5: 清理城市接口隐患
    - 5.1: 删除 `city.py` 中 heatmap 未使用的 `trend_skill` 调用
    - 5.2: 修复 `get_district` 找到区县后未跳出外层循环的问题
    - 5.3: 在 district 返回数据中补充所属 city 和 city_name
    - 5.4: 确认 `CityDistrict.tsx` 能兼容新增 city 字段

- [x] Task 6: 清理无效登录请求与优化发现页点赞失败处理
    - 6.1: 更新 `Login.tsx`，删除无意义的 `/users` 请求
    - 6.2: 保留固定体验用户入口和 Bowen 用户
    - 6.3: 更新 `SocialDiscover.tsx`，like 成功后再切换到下一张卡片
    - 6.4: like 失败时提示用户并保留当前卡片
    - 6.5: 防止重复点击造成并发请求

- [x] Task 7: 验证构建、接口和修复效果
    - 7.1: 运行前端构建验证 TypeScript 和 Vite 构建
    - 7.2: 运行后端关键文件语法检查
    - 7.3: Smoke test 通知、餐食图片、匹配、城市关键接口
    - 7.4: 检查本轮修改没有引入旧主题色残留
    - 7.5: 记录完成情况到 summary.md
