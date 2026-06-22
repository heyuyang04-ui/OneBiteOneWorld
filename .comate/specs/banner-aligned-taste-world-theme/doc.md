# 一食万象 Banner 对齐的前端主题重构说明

## 背景与目标
用户反馈当前前端整体渲染颜色与“一食万象 / One Bite, One World”的主题不符合。当前界面大量使用紫色、霓虹粉紫和通用白卡片风格，容易让产品像普通 AI/SaaS Demo，而不是“Agent 驱动的城市味觉感知系统”。

本次目标是让前端视觉与用户提供的 banner 保持一致：

- 深蓝黑黄昏城市背景
- 木质餐桌的暖棕色
- 碗与蒸汽的瓷白、雾灰
- 城市灯光的琥珀暖光
- “一箪食中照见个人生活轨迹，一味之间连接味觉同类，万千餐桌汇聚成城市级饮食智能”的温暖、电影感、城市智能气质

## 需求场景与处理逻辑

### 场景 1：登录 / 注册入口应像产品封面，而不是紫色模板页
处理逻辑：
- 使用深夜城市 + 餐桌暖光的渐变底色替代紫色霓虹背景。
- 登录主视觉强调“Agent 替人感知”“从每一顿饭看见更大世界”。
- 按钮、输入框、用户选择卡片改成琥珀、木色、瓷白和深色玻璃质感。

### 场景 2：首页应体现 L1 个人味觉档案和主动 Agent 感知
处理逻辑：
- `today-hero` 从紫色渐变改成“夜幕城市 + 暖光餐桌”的主视觉。
- 卡片从纯白卡片改成轻暖米白或深色玻璃卡片，统一阴影和边框。
- 标签、行动按钮使用琥珀/木色，不再使用紫色。

### 场景 3：味觉社交与匹配页应体现 L2 味觉同类连接
处理逻辑：
- 匹配卡片从白底通用社交卡片改为“味觉信号卡”：深色/暖色玻璃、琥珀匹配度、蒸汽感边缘高光。
- 头像渐变从紫橙改为城市蓝黑到餐桌琥珀。
- 标签风格统一为暖米色、木色文字。

### 场景 4：城市趋势、周报、餐食结果应体现 L3 城市味觉地图与洞察
处理逻辑：
- 周报主卡、趋势卡、餐食结果卡统一用城市夜色和暖光数据线表达“Agent 感知”。
- 去除 `#8B5CF6`、`#D946EF`、`#4C1D95` 等主视觉紫色。
- 保留少量蓝色作为城市夜景冷色，不作为霓虹科技风。

## 架构与技术方案

### 1. 建立统一 CSS 变量体系
修改 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/index.css`：

- 替换当前紫色变量：
  - `--app-bg`
  - `--app-shell-bg`
  - `--app-surface`
  - `--app-surface-strong`
  - `--app-text`
  - `--app-muted`
  - `--app-accent`
  - `--app-accent-2`
  - `--app-border`
- 新增或调整用于 banner 对齐的语义变量：
  - 夜色：`--app-night`, `--app-night-2`
  - 城市蓝：`--app-city-blue`
  - 木色：`--app-wood`, `--app-wood-deep`
  - 琥珀灯光：`--app-amber`, `--app-amber-soft`
  - 瓷白：`--app-porcelain`
  - 蒸汽雾灰：`--app-smoke`

预期方向示例：

```css
:root {
  --app-shell-bg: #050B10;
  --app-bg: #0B151B;
  --app-night: #071019;
  --app-night-2: #10202A;
  --app-city-blue: #244657;
  --app-wood: #9A6338;
  --app-wood-deep: #5C3822;
  --app-amber: #D9A35F;
  --app-amber-soft: #F1C987;
  --app-porcelain: #F4E8D4;
  --app-smoke: rgba(228, 232, 224, 0.68);
  --app-text: #F7EBD8;
  --app-muted: #B8AA97;
  --app-surface: rgba(18, 31, 38, 0.76);
  --app-surface-strong: rgba(31, 49, 58, 0.9);
  --app-border: rgba(241, 201, 135, 0.18);
}
```

### 2. 统一移动端外壳、顶部栏、底部导航
修改 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.css`：

- `.app-container` 改为深夜城市底色。
- `.app-header` 使用夜色到木色暖光的低饱和渐变。
- `.app-main` 去除突兀白色背景过渡，改成深色背景 + 暖米色内容层。
- `.tab-bar` 使用深色半透明玻璃；激活态使用琥珀色。

### 3. 登录注册页品牌化
修改 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`：

- 替换紫色 `radial-gradient`。
- `.login-page` 使用城市夜色、餐桌暖光和蒸汽感渐变。
- `.brand-mark`、`.auth-choice.primary`、`.login-submit` 改为琥珀/木色。
- 输入框和卡片使用深色玻璃 + 暖边框。

### 4. 首页、上传、餐食结果、周报主题统一
修改：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.css`

处理方式：
- 替换紫色变量和硬编码色。
- 保留卡片层级，但统一为瓷白暖底或深色玻璃。
- 按钮、进度条、徽章、扫描线使用琥珀色和木色。
- 强调 Agent 洞察时使用“暖光数据线”而不是紫色霓虹。

### 5. 味觉社交卡片和内联颜色清理
修改：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/MatchCard.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/SocialDiscover.tsx`
- 视检查结果同步处理其他页面内联颜色：
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchList.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchDetail.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/TasteProfile.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityRecommend.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`
  - `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx`

处理方式：
- 将硬编码紫色、粉紫、旧灰色标题替换为 CSS 变量或 banner 对齐色。
- 仅改样式，不改变业务逻辑、接口请求和数据结构。

## 受影响文件

### 必改文件
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/index.css`
  - 修改类型：全局主题变量、body 背景。
  - 影响范围：全应用基础色、字体色、背景色。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.css`
  - 修改类型：应用容器、头部、主区域、底部导航配色。
  - 影响组件：`Layout`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`
  - 修改类型：登录注册页背景、卡片、按钮、输入框主题。
  - 影响组件：`Login`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`
  - 修改类型：首页 hero、洞察卡片、推荐面板、快捷操作样式。
  - 影响组件：`Home`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.css`
  - 修改类型：上传区、扫描线、识别状态配色。
  - 影响组件：`ImageUpload`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`
  - 修改类型：结果卡、味觉条、徽章、下一餐建议样式。
  - 影响组件：`MealResult`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.css`
  - 修改类型：周报主卡、洞察徽章、指标格、信号卡样式。
  - 影响组件：`WeeklyReport`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/MatchCard.css`
  - 修改类型：匹配卡、头像、标签、匹配度、操作按钮样式。
  - 影响组件：`MatchCard`。

### 视检查结果调整文件
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/SocialDiscover.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchList.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchDetail.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/TasteProfile.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityRecommend.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx`

## 边界条件与异常处理

- 不修改后端接口、数据结构、登录逻辑、匹配逻辑和数据库。
- 不删除 Bowen 角色和已有演示数据。
- 不改变 `--app-max-width: 430px`，继续保证所有页面等宽渲染。
- 不引入新的 UI 框架，避免扩大依赖。
- 不使用用户 banner 文件作为网页背景依赖，避免路径、打包和版权/分辨率问题；本次通过色彩、渐变、质感对齐 banner。
- 若某些页面存在内联样式，优先替换颜色值，不做大规模组件重构。

## 数据流路径

本次主要是前端样式重构，业务数据流不变：

- 登录注册：`Login.tsx` → `/auth/*` API → localStorage → `Layout`
- 首页上传：`Home.tsx` / `ImageUpload.tsx` → `/meal/analyze` → `MealResult`
- 周报：`WeeklyReport.tsx` → `/report/weekly`
- 社交匹配：`SocialDiscover.tsx` / `MatchCard.tsx` → `/match/discover`
- 城市感知：`CityMap.tsx` / `CityTrends.tsx` / `CityRecommend.tsx` → `/city/*`

## 预期结果

- 全局视觉从紫色 AI 模板转为“黄昏城市 + 木质餐桌 + 琥珀灯光 + 蒸汽瓷白”的一食万象主题。
- 登录页、首页、上传、餐食结果、味觉社交、周报等核心页面风格统一。
- 三层 Agent 价值网络通过视觉语义更清晰：
  - L1：温暖、个人化、餐桌记忆。
  - L2：琥珀信号、味觉连接、低压力社交。
  - L3：深夜城市、聚合趋势、城市级感知。
- 前端构建通过 `npm run build`。
