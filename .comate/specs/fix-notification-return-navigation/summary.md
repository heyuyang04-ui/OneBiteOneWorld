# 修复提醒页返回导航总结

## 完成内容

本轮修复用户反馈的提醒页无法返回问题：

> 点了提醒，然后再想返回去，根本就回不去

## 修改文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`

## 具体改动

### 1. 新增路由导航能力

在 `Notifications.tsx` 中引入：

```tsx
import { useNavigate } from 'react-router-dom'
```

并在组件内创建：

```tsx
const navigate = useNavigate()
```

### 2. 新增返回逻辑

新增 `handleBack`：

```tsx
const handleBack = () => {
  if (window.history.length > 1) {
    navigate(-1)
    return
  }
  navigate('/home', { replace: true })
}
```

实现效果：

- 有浏览历史时返回上一页。
- 没有历史时回到 `/home`。

### 3. 新增提醒页头部操作区

将原本单独的标题改为：

- 左侧“返回”按钮。
- 中间标题“Agent 推送中心”。
- 右侧“回首页”按钮。

用户进入提醒中心后可以明确返回上一页或直接回首页。

### 4. 保留原有逻辑

以下逻辑未改变：

- 拉取通知列表。
- 空状态展示。
- 点击通知后调用 `/notifications/{id}/read` 标记已读。
- 已读/未读样式区分。

## 验证结果

执行前端构建：

```bash
npm run build
```

结果：通过。

构建存在 Vite chunk size warning，但不影响运行。

## 预期体验

现在用户点击顶部铃铛进入提醒页后：

- 点击“返回”会回到上一个页面。
- 如果直接打开提醒页，也可以返回首页。
- 点击“回首页”可直接回到首页。
