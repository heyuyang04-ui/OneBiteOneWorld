# Agent 架构改进记录

日期：2026-06-24

## 改动概览

针对原始 Agent 编排层的三个核心缺陷进行了修复，涉及 3 个文件。

---

## 缺陷一：LLM 解析失败静默处理

**问题**：`Decision.parse()` 在 JSON 解析失败时静默返回空决策，无日志、无重试，导致 Agent 什么都不做且难以排查。

**修改文件**：`backend/agents/protocol.py`、`backend/agents/base.py`

**改动内容**：
- `Decision` 新增 `_parse_failed: bool` 字段标记解析状态
- 解析失败时打印警告日志（含原始内容前 200 字符）
- `base.py` 的 ReAct 循环中，每次 LLM 调用失败时最多重试 1 次

---

## 缺陷二：单步规划无法动态调整（改为 ReAct 循环）

**问题**：原始 `run()` 一次 LLM 调用决定所有 skill，执行后无法根据结果调整，属于 Plan-then-Execute 模式。

**修改文件**：`backend/agents/base.py`

**改动内容**：
- `run()` 改为 ReAct 循环（最多 4 步）
- 每步执行 skill 后将结果作为 `observations` 追加进下一步 prompt
- LLM 返回 `skill_calls=[]` 时主动退出循环（任务完成信号）
- 新增 `_build_react_prompt()` 构建包含历史观察的动态 prompt

**循环结构**：
```
Thought → Skill Call → Observe Result → Thought → Next Skill Call → ... → Done
```

---

## 缺陷三：记忆无限增长，无 Token 感知

**问题**：`AgentMemory` 只有写入，无压缩机制；记忆条数无上限，每次只靠 `LIMIT 3` 截断取用，浪费且无法感知上下文占用。

**修改文件**：`backend/services/__init__.py`、`backend/agents/memory.py`、`backend/agents/base.py`

**改动内容**：

`services/__init__.py`：
- 新增 `MODEL_CONTEXT_WINDOWS` 映射（GPT-5.5=200K，gpt-4o=128K 等）
- 新增 `chat_with_usage()` 方法，返回 `(content, usage)`，usage 含 `context_ratio = prompt_tokens / context_window`

`agents/memory.py`：
- 新增 `maybe_compress(context_ratio)` 方法
- 触发阈值：**50%**（对齐 Mem0/Hermes 生产标准）
- 超阈值时用 LLM 将旧记录压缩成一条摘要，保留最新 5 条不动

`agents/base.py`：
- ReAct 循环改用 `chat_with_usage()` 获取真实 token 用量
- 每步开始前检查 `context_ratio >= 0.5`，满足则同步压缩记忆并刷新上下文
- 每步打印 token 占用日志

**压缩触发示例日志**：
```
[Token] 个人味觉分析师 step=1 context=61% (122000/200000)
[Memory] user=u123 context_ratio=61.0% → compressed 18 records → 1 summary
```

---

## 阈值选择依据

| 框架 | 触发阈值 |
|---|---|
| Mem0 / Hermes（生产） | 50% |
| Claude Code | ~75% |
| LangGraph 官方建议 | 70% |
| 本项目（ReAct 多步） | **50%** |

选择 50% 的原因：ReAct 循环每步追加 observations 导致 prompt 快速增长，需留足后续步骤空间。
