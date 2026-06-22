# 一食万象 Demo 缺陷修复方案

## 需求背景

基于三份文档（用户介绍书、PRD文档、技术架构文档）与现有代码的全面对比分析，识别出以下影响 Hackathon Demo 质量的关键缺陷，需要在保证现有功能正常运行的前提下逐一修复。

---

## 修复范围

### P0 — 阻塞 Demo 体验

#### 1. 修复匹配逻辑 Bug
- **位置**: `backend/routers/match.py:32-34`
- **问题**: `match_id` 被同时当作 `user_a` 和 SQL 查询中的 `user_b` 使用，导致 like 操作时找不到匹配记录
- **修复**: 分离 `match_id`（匹配记录 ID）和 `other_user_id`（对方用户 ID）的概念
- **影响文件**: `backend/routers/match.py`

#### 2. 增加用户切换机制
- **位置**: `backend/main.py:31`
- **问题**: 中间件硬编码默认用户为 `user_01`，500 个 mock 用户只能体验一个视角；前端无切换入口
- **修复方案**:
  - 后端：增加 `PUT /api/users/me/switch` 接口，支持切换当前用户
  - 前端：在 Settings 页面或 Layout 增加用户切换下拉框
- **影响文件**: `backend/routers/users.py`, `frontend/src/pages/Settings.tsx`, `frontend/src/components/Layout.tsx`

---

### P1 — 影响核心价值展示

#### 3. 实现实时推送（SSE 替代 WebSocket）
- **问题**: 技术文档承诺 WebSocket 实时推送但未实现；产品介绍强调"Agent 主动推送洞察"
- **修复方案**: 用 Server-Sent Events (SSE) 替代 WebSocket，降低实现复杂度：
  - 后端：新增 `GET /api/notifications/stream` SSE 端点，定时检查新通知
  - 前端：在 Layout 层订阅 SSE，收到新通知时刷新未读计数
- **影响文件**: `backend/routers/notifications.py`, `frontend/src/components/Layout.tsx`

#### 4. 修复图片存储
- **位置**: `backend/routers/meals.py:31`
- **问题**: 上传餐食时 `image_url=""`，照片上传后 URL 为空
- **修复**: 将 base64 图片保存为本地文件，存储文件路径到 `image_url`
- **影响文件**: `backend/routers/meals.py`, `backend/config.py`

#### 5. 隐私设置数据隔离
- **位置**: `backend/skills/vector_skill.py:122`, `backend/skills/match_skill.py:40`
- **问题**: `private` 用户仅在匹配时跳过，但味觉向量仍存储；PRD 承诺"可随时退出匹配池、删除味觉向量"
- **修复**:
  - 匹配发现时检查隐私级别（已有，逻辑正确但需确认完整）
  - 增加隐私级别变更时同步清理匹配记录
- **影响文件**: `backend/routers/users.py`

#### 6. CORS 策略收紧
- **位置**: `backend/main.py:12`
- **问题**: `allow_origins=["*"]` 配合 `allow_credentials=True` 存在安全风险
- **修复**: 移除 `*` 通配符，改为精确的允许域名列表 `["http://localhost:5173", "http://localhost:3000"]`
- **影响文件**: `backend/main.py`

#### 7. 全局异常处理器安全加固
- **位置**: `backend/main.py:19-25`
- **问题**: `str(exc)` 可能暴露内部敏感信息给前端
- **修复**: 返回通用错误消息，仅在开发环境打印详细堆栈
- **影响文件**: `backend/main.py`

---

### P2 — 锦上添花

#### 8. 周报加入反思问题
- **位置**: `backend/skills/report_skill.py`
- **问题**: PRD 提到 reflection question，但 Prompt 未要求生成
- **修复**: 在 LLM Prompt 中增加反思问题生成要求
- **影响文件**: `backend/skills/report_skill.py`

#### 9. 城市推荐 × 个人口味交叉
- **位置**: `backend/routers/city.py:59-67`
- **问题**: `city/recommend` 接口分开返回餐厅推荐和趋势推荐，未做交叉
- **修复**: 增加交叉推荐逻辑：将城市趋势与用户口味匹配，生成"你可能喜欢的新趋势"推荐
- **影响文件**: `backend/skills/recommend_skill.py`

#### 10. 增加删除餐食 API
- **问题**: PRD 承诺"可删掉任何不想保留的记录"，但无删除 API
- **修复**: 新增 `DELETE /api/meals/{meal_id}` 端点
- **影响文件**: `backend/routers/meals.py`

#### 11. 统一文件读取路径
- **问题**: 多处使用相对路径 `open("data/mock_city.json")`，依赖 cwd
- **修复**: 统一使用 `os.path.dirname(__file__)` 构建绝对路径
- **影响文件**: `backend/routers/city.py`, `backend/skills/match_skill.py`, `backend/skills/recommend_skill.py`, `backend/skills/trend_skill.py`

---

## 不做修改

- **API Key 硬编码**: 按用户要求不修改

