# 扩展并净化味觉匹配发现任务计划

- [x] Task 1: 更新后端匹配发现技能
    - 1.1: 让 `match_skill` 接收并传递 `limit` 参数
    - 1.2: 将 `_discover_matches` 默认候选数量提升到 20，并限制最大 50
    - 1.3: 增加内部测试账号过滤逻辑，屏蔽包含测试、冒烟、test、smoke、validation 的用户
    - 1.4: 增加 taste vector 和 tags 的容错解析，跳过异常候选
    - 1.5: 保持现有相似度、维度分数、common 和 diff 计算逻辑

- [x] Task 2: 更新后端匹配路由展示逻辑
    - 2.1: 将 `/match/discover` 默认 `limit` 改为 20，并做 1 到 50 的边界限制
    - 2.2: 将限定后的 `limit` 传给 `match_skill`
    - 2.3: 用确定性解释替代发现接口中的 LLM 逐个解释调用
    - 2.4: 在 `/match/list` 中过滤历史匹配列表里的内部测试账号

- [x] Task 3: 更新前端味觉发现请求
    - 3.1: 将 `SocialDiscover.tsx` 的发现请求从 `limit=5` 改为 `limit=20`
    - 3.2: 保留候选进度展示，确保用户能看到更大的推荐池数量
    - 3.3: 检查空态和加载态文案不暴露测试语义

- [x] Task 4: 验证匹配发现与构建结果
    - 4.1: 调用 `/api/match/discover?limit=20` 验证候选数量增加
    - 4.2: 检查返回用户名称不包含测试、冒烟、test、smoke、validation
    - 4.3: 验证 `/api/match/list` 不展示测试账号
    - 4.4: 执行前端构建，确认 TypeScript 和 Vite 构建通过
