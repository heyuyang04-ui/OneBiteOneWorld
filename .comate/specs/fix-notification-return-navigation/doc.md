# 修复提醒页无法返回的导航问题说明

## 背景与问题

用户反馈：“点了提醒，然后再想返回去，根本就回不去”。

当前实现中：

- 顶部铃铛入口位于 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`。
- 点击铃铛会进入 `/notifications`。
- 提醒页文件为 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`。
- 提醒页只展示通知列表，没有页面级返回按钮、回首页按钮或历史返回逻辑。
- 底部 Tab 只包含：首页、味觉、发现、城市；不包含提醒页。

因此用户从提醒中心进入后，如果不知道底部 Tab 可以回到其他模块，或者页面滚动/视觉焦点让底部导航不明显，就会形成“回不去”的体验。

## 修复目标

为提醒页增加明确、稳定的返回路径：

1. 页面顶部提供“返回”按钮。
2. 如果浏览器历史栈可返回，则优先返回上一页。
3. 如果没有可返回历史，则回到 `/home`。
4. 页面同时提供“回首页”辅助入口，避免用户迷路。
5. 保持现有通知读取和标记已读逻辑不变。

## 技术方案

### 前端 Notifications 页面

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`

改动：

- 引入 `useNavigate`。
- 新增 `handleBack` 函数。
- 页面头部从单独标题改成带返回操作的 header。
- 返回逻辑：

```tsx
const navigate = useNavigate()

const handleBack = () => {
  if (window.history.length > 1) {
    navigate(-1)
  } else {
    navigate('/home', { replace: true })
  }
}
```

- 增加“回首页”按钮：

```tsx
<button type="button" onClick={() => navigate('/home')}>回首页</button>
```

### 样式策略

当前 `Notifications.tsx` 使用内联样式，没有单独 CSS 文件。本轮保持最小改动，继续使用内联样式，避免为一个小修复引入额外样式文件。

## 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`
  - 新增 `useNavigate`
  - 新增 `handleBack`
  - 新增提醒页头部返回区
  - 保留 `markRead` 和通知列表渲染逻辑

## 边界条件

- 从首页点击铃铛进入提醒页：点击返回应回首页。
- 从其他页面点击铃铛进入提醒页：点击返回应回到之前页面。
- 直接打开 `/notifications`：点击返回应进入 `/home`。
- 没有通知时仍显示返回和回首页入口。
- 标记已读功能不受影响。

## 数据流

```text
用户点击顶部铃铛
  -> 路由进入 /notifications
  -> Notifications 页面展示返回按钮
  -> 用户点击返回
  -> 有历史：navigate(-1)
  -> 无历史：navigate('/home', { replace: true })
```

## 验证计划

1. 前端构建：

```bash
npm run build
```

2. 手动验证：

- 从首页点击铃铛进入提醒页，再点击返回。
- 从发现页点击铃铛进入提醒页，再点击返回。
- 直接访问 `/notifications`，点击返回或回首页。
- 点击通知项，确认仍可标记已读。

## 预期结果

用户进入提醒中心后，可以明确返回上一页或首页，不再出现“点进提醒后回不去”的体验问题。
