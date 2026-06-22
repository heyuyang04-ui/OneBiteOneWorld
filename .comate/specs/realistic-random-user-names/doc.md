# 真实感随机虚拟用户姓名

## 需求场景与处理逻辑

用户在味觉匹配推荐中看到的候选名字过于假，例如 `大鹏`、`阿强`、`小鱼`、`萌萌`，以及大量由 `小/老/大/阿 + 单字` 拼出来的昵称。这会让产品像测试数据，而不是一个真实社交应用。

本次改动目标：

1. 将系统内置 mock 用户名字替换为更自然的随机虚拟姓名。
2. 避免明显机器拼接感的名字，例如：
   - `大鹏涵`
   - `老莉浩`
   - `阿强曦`
   - `大鱼鱼`
   - 单字名如 `杰`、`鹏`、`涵`
3. 保留关键用户 `Bowen` 不改。
4. 同步更新当前 SQLite 数据库中已有 mock 用户姓名，避免前端继续读到旧名字。
5. 不修改登录注册逻辑，不修改 API Key 配置。

## 架构与技术方案

当前用户数据来源：

- 初始 mock 数据：`/Users/libowen/Desktop/one-bite-one-world/backend/data/mock_users.json`
- 运行时数据库：`/Users/libowen/Desktop/one-bite-one-world/backend/demo.db`
- 数据导入逻辑：`/Users/libowen/Desktop/one-bite-one-world/backend/database.py`

`database.py` 只在 `users` 表为空时导入 mock 数据：

```py
cursor = await db.execute("SELECT COUNT(*) FROM users")
row = await cursor.fetchone()
if row[0] == 0:
    await _import_mock_data(db)
```

因此只修改 `mock_users.json` 不会影响当前已经运行的 `demo.db`。需要做两层处理：

1. 更新 `mock_users.json`，保证后续重建数据库时名字自然。
2. 更新当前 `demo.db` 中同一批 mock 用户的 `name` 字段，保证现有服务立刻生效。

## 姓名生成策略

使用固定随机种子生成虚拟中文姓名，确保每次执行结果稳定、可复现。

### 姓名风格

使用真实常见姓氏 + 现代常见名字组合，例如：

- 林知夏
- 陈屿白
- 周南星
- 许清和
- 苏明远
- 梁若宁
- 沈予安
- 顾一然
- 唐景行
- 何沐辰

姓名规则：

- 以 2-3 个中文字符为主。
- 优先生成 `姓 + 双字名`。
- 少量生成 `姓 + 单字名`，但避免大量单字重复。
- 不使用 `小/老/大/阿` 作为系统批量前缀。
- 不生成带测试含义的名字。
- 不生成真实公众人物或敏感姓名。
- 所有 mock 用户内尽量唯一。

### 保留规则

不修改以下用户：

- `user_bowen`：保留 `Bowen`
- 注册用户：不批量修改用户自己填写的名字

对于 `user_01` 等内置体验用户，可以改成更自然的虚拟姓名。

## 受影响文件

### `/Users/libowen/Desktop/one-bite-one-world/backend/data/mock_users.json`

修改类型：批量更新 mock 用户 `name` 字段。

影响范围：

- 所有 `id` 形如 `user_01`、`user_02`、`user_500` 的 mock 用户。
- 跳过 `user_bowen`。

处理逻辑示例：

```py
for user in users:
    if user["id"] == "user_bowen":
        continue
    user["name"] = generated_names[index]
```

### `/Users/libowen/Desktop/one-bite-one-world/backend/demo.db`

修改类型：同步更新当前数据库中的 mock 用户姓名。

影响范围：

- 更新 `users` 表中 mock 用户 ID 对应的 `name` 字段。
- 跳过：
  - `user_bowen`
  - 非 mock 注册用户，例如 `user_` + uuid 短 ID

处理逻辑示例：

```sql
UPDATE users SET name = ? WHERE id = ?
```

### 可选临时脚本

为避免手工编辑 500 条 JSON，使用一次性 Python 脚本执行数据更新。脚本只作为执行手段，不需要长期保留到项目代码中。

## 数据流路径

1. 读取 `backend/data/mock_users.json`。
2. 根据固定姓名池和随机种子生成足够数量的虚拟姓名。
3. 按 mock 用户顺序更新 `name` 字段。
4. 写回 `mock_users.json`。
5. 打开 `backend/demo.db`。
6. 对同 ID 的 mock 用户同步执行 `UPDATE users SET name=? WHERE id=?`。
7. 调用 `/api/match/discover?limit=20` 验证推荐页姓名变化。

## 边界条件与异常处理

- 如果 `mock_users.json` 不存在或 JSON 解析失败，停止执行，不改数据库。
- 如果生成姓名数量不足，停止执行，避免重复名字过多。
- 如果当前数据库不存在，只更新 JSON；下次启动时会由 mock 数据导入。
- 不修改 `Bowen`。
- 不修改用户自行注册的真实名字。
- 不删除任何用户、餐食、匹配记录。

## 预期结果

1. 推荐匹配页不再出现明显假昵称，例如 `大鹏`、`阿强`、`萌萌`、`老xx`、`小xx`、`大xx` 批量命名风格。
2. `/api/match/discover?limit=20` 返回的候选用户姓名更像真实虚拟用户。
3. `mock_users.json` 和当前 `demo.db` 保持一致。
4. `Bowen` 仍保留。
5. 前端无需改动，构建不受影响。

## 验证方式

- 验证 `mock_users.json`：
  - `user_bowen` 名字仍为 `Bowen`
  - 前 20 个 mock 用户姓名为自然中文虚拟姓名
  - 无明显批量前缀风格
- 验证接口：
  - 请求 `/api/match/discover?limit=20`
  - 检查返回姓名自然，且不包含测试用户
- 验证数据一致性：
  - 当前数据库 `users` 表对应 mock 用户姓名已更新
