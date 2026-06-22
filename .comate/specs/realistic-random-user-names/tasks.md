# 真实感随机虚拟用户姓名任务计划

- [x] Task 1: 生成真实感虚拟姓名映射
    - 1.1: 读取 `backend/data/mock_users.json` 并识别所有内置 mock 用户
    - 1.2: 跳过 `user_bowen`，保留 Bowen 名字不变
    - 1.3: 使用固定随机种子生成常见姓氏 + 现代双字名的姓名池
    - 1.4: 检查生成姓名唯一性，避免测试、冒烟、小/老/大/阿批量前缀风格

- [x] Task 2: 更新 mock 用户源数据
    - 2.1: 将生成的姓名映射写回 `backend/data/mock_users.json`
    - 2.2: 保留每个用户的 id、city、age、occupation、tags、taste_vector、privacy_level 不变
    - 2.3: 验证 `user_bowen` 仍为 Bowen
    - 2.4: 抽查前 20 个 mock 用户姓名，确认不再是明显假昵称

- [x] Task 3: 同步更新当前 SQLite 数据库
    - 3.1: 打开 `backend/demo.db` 并定位 `users` 表内置 mock 用户
    - 3.2: 按姓名映射更新数据库中的 mock 用户 `name` 字段
    - 3.3: 跳过注册用户和 `user_bowen`
    - 3.4: 确认不删除任何用户、餐食或匹配记录

- [x] Task 4: 验证推荐匹配姓名展示
    - 4.1: 调用 `/api/match/discover?limit=20` 验证候选姓名已更新
    - 4.2: 检查返回姓名不包含测试、冒烟、test、smoke、validation
    - 4.3: 检查返回姓名不再出现明显批量前缀风格
    - 4.4: 确认 `Bowen` 仍可在用户数据中保留
