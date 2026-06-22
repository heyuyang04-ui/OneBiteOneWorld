# fixpoint-followup-hardening 需求说明

## 背景

`/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt` 是复查更新版，上一轮 20 个问题大部分已修复，目前仍记录 4 个问题：

- BUG-1：`backend/config.py` 中仍有硬编码 AI API Key fallback。
- BUG-2：`matches` 表缺少 `(user_a, user_b)` 唯一约束，并发 like 仍可能重复。
- BUG-3：上传成功后通过路由 state 进入 `MealResult` 时看不到照片，刷新后才显示。
- BUG-4：上传图片落盘前缺少服务端大小和类型校验。

本轮处理策略：

- BUG-1 本轮不修改。原因：用户此前明确要求保留 `backend/config.py` 中的 hardcoded API key fallback；并且当前 `code-security` skill 明确硬编码凭证修复与托管功能暂未开放。因此本轮仅在说明中记录风险，不改动 `backend/config.py`。
- BUG-2、BUG-3、BUG-4 执行增量修复。

## 需求一：为 matches 增加数据库级唯一兜底

### 场景与处理逻辑

当前 `backend/routers/match.py` 已在 like 插入前做 SELECT 查重，单线程重复点击可以避免重复数据。但在并发请求下，两个请求可能同时通过查重并分别插入 pending 记录。由于 `backend/database.py` 中 `matches` 表没有 `(user_a, user_b)` 唯一约束，`INSERT OR IGNORE` 没有真正的冲突目标，无法防止重复。

处理逻辑：

1. 保留现有应用层查重逻辑。
2. 在数据库初始化时增加迁移式修复：先清理已存在的重复 `(user_a, user_b)` 记录，再创建唯一索引。
3. 使用 `CREATE UNIQUE INDEX IF NOT EXISTS` 支持已有 SQLite 数据库；仅修改 `CREATE TABLE IF NOT EXISTS` 不会影响现有表结构，因此必须有索引迁移。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`：

- 在 `init_db()` 创建表并 commit 前后增加 `_ensure_match_unique_index(db)`。
- 新增内部函数：

```py
async def _ensure_match_unique_index(db):
    await db.execute("""
        DELETE FROM matches
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM matches
            GROUP BY user_a, user_b
        )
    """)
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_user_pair ON matches(user_a, user_b)"
    )
```

说明：

- 使用 `MIN(rowid)` 保留每组现有重复记录中的第一条，删除其余重复项。
- 索引名固定为 `idx_matches_user_pair`。
- `(user_a, user_b)` 表示有向关系；`A like B` 与 `B like A` 是两条不同方向记录，仍可共同存在，用于 mutual 判断。

### 影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/database.py`
  - `init_db()`：调用唯一索引迁移逻辑。
  - 新增 `_ensure_match_unique_index()`：去重并创建唯一索引。

### 边界与异常

- 若 `matches` 表为空，DELETE 不影响数据，索引正常创建。
- 若已有重复记录，保留最早 rowid 对应记录。
- 若索引已存在，`IF NOT EXISTS` 不重复创建。
- 不改变 mutual 匹配方向模型。

### 预期结果

并发 like 即使同时越过应用层查重，也会被数据库唯一索引兜底，避免同一用户对同一目标重复产生多条 match 记录。

## 需求二：MealResult 在 state.meal 无 image 时补拉图片

### 场景与处理逻辑

上传接口 `POST /api/meals` 返回的 `meal_payload` 包含 `image_url`，但为了避免响应体过大，不返回 base64 图片。首页上传成功后会携带 `state.meal` 跳转到 `MealResult`，此时页面直接渲染 `meal.image`，导致照片缺失。刷新后 `GET /meals/:id` 会返回 `image`，所以刷新后可见。

处理逻辑：

1. 保持上传响应不携带 base64 图片，避免大响应体。
2. 在 `MealResult.tsx` 中，当已有 `meal.id` 但 `meal.image` 为空时，请求 `GET /meals/{id}/image`。
3. 成功后将 `{ image }` 合并进当前 meal state，页面自动显示照片。
4. 图片加载失败不阻断页面核心识别结果展示。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`：

```tsx
useEffect(() => {
  if (!meal?.id || meal.image) return
  api.get(`/meals/${meal.id}/image`).then(res => {
    const image = res.data.data?.image
    if (res.data.success && image) {
      setMeal((prev: any) => prev ? { ...prev, image } : prev)
    }
  }).catch(() => {})
}, [meal?.id, meal?.image])
```

### 影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
  - 新增图片补拉 `useEffect`。

### 边界与异常

- 如果是刷新进入且 `GET /meals/:id` 已返回 `image`，不会重复请求图片。
- 如果 `state.meal` 没有 id，不发请求。
- 如果图片接口返回失败，仅不展示照片，不影响餐食名称、口味、营养、建议等内容。

### 预期结果

拍照上传成功后立即进入结果页也能自动显示刚上传的照片，不需要手动刷新。

## 需求三：上传图片服务端大小与类型校验

### 场景与处理逻辑

当前 `backend/routers/meals.py` 对前端传来的 base64 字符串直接调用 `base64.b64decode` 并写入 `{meal_id}.jpg`，缺少服务端校验。前端压缩不能作为安全边界，后端需要拒绝过大或非图片内容。

处理逻辑：

1. 在调用 `vision_skill` 和写盘前先校验 `body.image`。
2. 解码 base64 时启用严格校验。
3. 检查解码后大小上限。
4. 使用 magic number 判断真实图片类型。
5. 仅允许常见安全图片格式：JPEG、PNG、WebP。
6. 根据真实格式选择落盘扩展名，不再固定写成 `.jpg`。
7. 校验失败时返回明确错误，不继续调用识别或写盘。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`：

新增常量与工具函数：

```py
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _decode_image(image_base64: str) -> bytes:
    try:
        return base64.b64decode(image_base64, validate=True)
    except Exception:
        raise ValueError("图片数据格式不正确")


def _detect_image_extension(img_data: bytes) -> str:
    if img_data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if img_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(img_data) >= 12 and img_data[:4] == b"RIFF" and img_data[8:12] == b"WEBP":
        return "webp"
    raise ValueError("仅支持 JPG、PNG 或 WebP 图片")


def _validate_image(image_base64: str) -> tuple[bytes, str]:
    img_data = _decode_image(image_base64)
    if not img_data:
        raise ValueError("图片不能为空")
    if len(img_data) > MAX_IMAGE_BYTES:
        raise ValueError("图片不能超过 5MB")
    ext = _detect_image_extension(img_data)
    return img_data, ext
```

在 `upload_meal()` 开头执行：

```py
try:
    img_data, image_ext = _validate_image(body.image)
except ValueError as exc:
    return {"success": False, "error": {"message": str(exc)}}
```

写盘时：

```py
image_path = os.path.join(app_config.image_dir, f"{meal_id}.{image_ext}")
with open(image_path, "wb") as f:
    f.write(img_data)
```

### 影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - 新增图片校验工具函数。
  - `upload_meal()` 调整为先校验，再识别，再写盘。
  - 失败返回 `success: False`，避免静默跳过保存。

### 边界与异常

- 非 base64：返回 `图片数据格式不正确`。
- 空图片：返回 `图片不能为空`。
- 超过 5MB：返回 `图片不能超过 5MB`。
- 非 JPEG/PNG/WebP：返回 `仅支持 JPG、PNG 或 WebP 图片`。
- 合法图片：继续识别、保存、建档、更新画像。

### 预期结果

服务端不再信任客户端压缩结果，能拒绝异常大文件和伪装成图片的非图片内容，同时不影响正常拍照上传体验。

## 数据流

### 上传成功后图片展示

1. 首页压缩/采集图片并调用 `POST /api/meals`。
2. 后端校验 base64、大小、magic number。
3. 后端调用视觉识别、保存真实图片文件、写入 `meals.image_url`。
4. 前端拿到 `meal_payload` 并跳转 `MealResult`。
5. `MealResult` 发现 `meal.id` 存在但 `meal.image` 不存在。
6. 前端调用 `GET /api/meals/{id}/image`。
7. 接口返回 base64，页面合并 state 并渲染 `<img>`。

### like 并发去重

1. 用户 A 对用户 B 发起 like。
2. 应用层先查已有 pending/mutual。
3. 若并发下多个请求同时进入插入，SQLite 唯一索引 `idx_matches_user_pair` 对 `(user_a,user_b)` 做兜底。
4. 重复插入被忽略或失败处理为已有关系，避免重复脏数据。

## 验证方案

- 后端语法验证：对修改后的 Python 文件执行编译检查。
- 前端构建验证：执行 Vite build，确保 TypeScript/React 编译通过。
- 数据库验证：启动或调用 `init_db()` 后检查 `idx_matches_user_pair` 存在。
- 上传验证：
  - 合法图片上传成功。
  - 非 base64/非图片/超大图片返回 `success: False`。
- 结果页验证：携带 `state.meal` 且无 `image` 时，会请求 `/meals/{id}/image` 并展示图片。

## 不在本轮修改的内容

- 不修改 `/Users/libowen/Desktop/one-bite-one-world/backend/config.py` 中 AI API Key fallback。
- 不执行密钥轮换、Git 历史清理或凭证托管。
- 不改变现有用户模型、匹配算法和 UI 主题。