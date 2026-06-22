# confirm-before-meal-recognition 修复总结

## 问题

新增“食物描述”后，原流程仍然是：用户一选择图片，`ImageUpload` 立即调用 `onUpload(base64)`，`Home.tsx` 立刻请求 `/api/meals` 触发 AI 识别。

这会导致用户还没输入或修改描述，AI 已经开始识别，违背“照片 + 描述一起给大模型”的设计目标。

## 已完成修改

### 1. ImageUpload 不再自动识别

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.tsx`

完成内容：

- props 从：

```tsx
onUpload: (base64: string) => void
```

改为：

```tsx
onImageReady: (base64: string) => void
```

- 选择图片后只做两件事：
  - 设置 preview。
  - 把 base64 回传给父组件。

不再触发后端识别。

### 2. Home 拆分“选择图片”和“确认识别”

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`

完成内容：

- 新增：

```tsx
const [pendingImage, setPendingImage] = useState('')
```

- 新增：

```tsx
const handleImageReady = (base64: string) => {
  setPendingImage(base64)
}
```

- 原来的上传识别逻辑改为：

```tsx
const handleConfirmRecognition = async () => {
  if (!pendingImage || loading) return
  const res = await api.post('/meals', {
    image: pendingImage,
    description: foodDescription.trim(),
  })
}
```

现在只有点击确认按钮后才请求 `/api/meals`。

### 3. 新增确认识别按钮

在记录区新增按钮状态：

- 未选择图片：

```text
请先选择照片
```

按钮禁用。

- 已选择图片：

```text
确认识别这一餐
```

按钮可点击。

- 识别中：

```text
Agent 正在识别...
```

按钮禁用。

同时新增“重新选择照片”按钮，允许清空当前预览图。

### 4. 失败时清空图片但保留描述

以下场景会清空图片预览和 `pendingImage`：

- 上传失败。
- 非食物。
- 识别结果异常。
- 网络异常。

描述 `foodDescription` 会保留，方便用户修改描述后重新选择图片识别。

### 5. 样式适配

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`

新增样式：

- `.recognition-actions`
- `.confirm-recognition-btn`
- `.change-photo-btn`
- disabled 状态样式

保持当前夜色 / 木质 / 琥珀主题。

## 验证结果

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

### 静态检查

检查结果：

```text
ImageUpload.tsx 只暴露 onImageReady
ImageUpload.tsx 选择图片后只调用 onImageReady(base64)
Home.tsx 只有 handleConfirmRecognition 中调用 api.post('/meals')
确认按钮 onClick 绑定 handleConfirmRecognition
```

结论：

- 选择图片后不会立即识别。
- 用户可以先选图、填写描述，再点击确认识别。
- `/api/meals` 只会在确认按钮流程中调用。

## 当前服务说明

本次只修改前端。当前 Vite 前端服务支持 HMR，通常会自动热更新：

```text
http://localhost:5173/
```

如果页面未更新，刷新浏览器即可。

## 任务状态

`.comate/specs/confirm-before-meal-recognition/tasks.md` 中 5 个顶层任务均已完成。