# fixpoint-followup-hardening 修复总结

## 本轮处理范围

根据 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt` 复查更新版，本轮处理以下问题：

- BUG-2：`matches` 表缺唯一约束，并发 like 仍可能重复。
- BUG-3：上传成功后跳转 `MealResult` 看不到照片。
- BUG-4：上传图片落盘前缺少服务端大小与类型校验。

BUG-1（硬编码 AI API Key fallback）本轮未修改，原因是此前已明确要求保留 `backend/config.py` 中的 fallback，且当前代码安全 skill 的硬编码凭证修复与托管流程暂未开放。

## 已完成修改

### 1. matches 数据库级唯一兜底

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`

完成内容：

- 新增 `_ensure_match_unique_index(db)`。
- 初始化数据库时先清理已存在的重复 `(user_a, user_b)` match 记录。
- 创建唯一索引：`idx_matches_user_pair ON matches(user_a, user_b)`。
- 保持 `(user_a, user_b)` 为有向关系，不影响互相匹配模型。

效果：

- 应用层查重之外，数据库层也能兜底防止并发重复 like。

### 2. MealResult 上传后补拉图片

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`

完成内容：

- 当 `state.meal` 已存在但缺少 `image` 时，自动调用 `GET /meals/{id}/image`。
- 成功后把 base64 图片合并进当前 meal state。
- 图片补拉失败不影响餐食详情主体展示。

效果：

- 上传成功后立即进入结果页也能显示照片，不再依赖手动刷新。

### 3. 上传图片服务端校验

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`

完成内容：

- 新增 `MAX_IMAGE_BYTES = 5 * 1024 * 1024`。
- 使用 `base64.b64decode(..., validate=True)` 严格校验 base64。
- 拒绝空图片。
- 拒绝超过 5MB 的图片。
- 使用 magic number 识别并仅允许 JPG、PNG、WebP。
- 在调用视觉识别和写盘前完成校验。
- 按真实图片类型保存 `.jpg`、`.png` 或 `.webp` 文件。

效果：

- 后端不再信任客户端压缩结果，能拒绝异常大文件和非图片内容。

## 验证结果

### 后端语法检查

命令：

```bash
python3 -m py_compile backend/database.py backend/routers/meals.py
```

结果：通过。

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

Vite 构建成功，仅保留原有 chunk size warning，不影响运行。

### 数据库唯一索引验证

执行 `init_db()` 后检查 SQLite 索引：

```text
idx_matches_user_pair
columns: user_a, user_b
unique: true
```

结果：通过。

## 任务状态

`.comate/specs/fixpoint-followup-hardening/tasks.md` 中 4 个顶层任务均已完成。