# confirm-before-meal-recognition 需求说明

## 背景

当前 `ImageUpload` 在用户选择图片后，会立即调用 `onUpload(base64)`，而 `Home.tsx` 的 `handleUpload()` 会马上请求 `/api/meals` 触发 AI 识别。这和新增“用户描述食物是什么”的设计冲突：用户刚选择完图片，还没来得及输入文字，AI 已经开始识别。

用户要求：上传完图片后，需要点击“确认识别”才可以开始识别。这样用户可以先选图、看预览、补充描述，再统一提交给大模型。

## 目标

- 选择图片后只生成预览和 base64，不自动调用后端识别。
- 用户可以在预览状态下继续填写或修改描述。
- 点击“确认识别”后，前端才提交 `{ image, description }` 给 `/api/meals`。
- 用户可重新选择图片。
- loading 时禁止重复提交。

## 需求一：ImageUpload 从自动上传改为图片选择回调

### 当前逻辑

`ImageUpload.tsx` 当前 props：

```tsx
interface ImageUploadProps {
  onUpload: (base64: string) => void
  loading?: boolean
  resetKey?: number
}
```

选择文件后立即：

```tsx
onUpload(base64)
```

### 修改方案

将语义改为：

```tsx
interface ImageUploadProps {
  onImageReady: (base64: string) => void
  loading?: boolean
  resetKey?: number
}
```

选择文件后：

```tsx
setPreview(dataUrl)
onImageReady(base64)
```

不再调用后端。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.tsx`

## 需求二：首页增加 pending image 状态和确认识别按钮

### 当前逻辑

`Home.tsx` 当前：

```tsx
<ImageUpload onUpload={handleUpload} loading={loading} resetKey={uploadResetKey} />
```

`handleUpload(base64)` 同时承担“接收图片”和“提交识别”。

### 修改方案

新增状态：

```tsx
const [pendingImage, setPendingImage] = useState('')
```

拆分逻辑：

```tsx
const handleImageReady = (base64: string) => {
  setPendingImage(base64)
}

const handleConfirmRecognition = async () => {
  if (!pendingImage || loading) return
  const res = await api.post('/meals', {
    image: pendingImage,
    description: foodDescription.trim(),
  })
}
```

渲染：

```tsx
<ImageUpload onImageReady={handleImageReady} loading={loading} resetKey={uploadResetKey} />
<button disabled={!pendingImage || loading} onClick={handleConfirmRecognition}>确认识别</button>
```

失败时：

- 清空图片预览和 pendingImage。
- 保留 description，方便用户修改后重试。

成功时：

- 跳转 `MealResult`。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`

## 需求三：交互文案与样式

### 文案

- 未选择图片：按钮禁用，文案“请先选择照片”。
- 已选择图片：按钮可用，文案“确认识别这一餐”。
- loading：文案“Agent 正在识别...”

### 样式

新增或复用 Home.css：

- `.recognition-actions`
- `.confirm-recognition-btn`
- disabled 状态样式。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`

## 数据流

1. 用户选择图片。
2. `ImageUpload` 压缩图片，生成 preview 和 base64。
3. `ImageUpload` 调用 `onImageReady(base64)`。
4. `Home` 将 base64 保存到 `pendingImage`。
5. 用户填写/修改描述。
6. 用户点击“确认识别这一餐”。
7. `Home` 调用 `/api/meals`，提交 `pendingImage + foodDescription`。
8. 后端将图文一起传给大模型。
9. 成功后跳转结果页。

## 边界条件

- 没有选择图片时不能提交识别。
- loading 时不能重复点击。
- 识别失败/非食物/结果异常时清空图片预览，但保留文字描述。
- resetKey 变化时，ImageUpload 清空 preview；Home 同步清空 pendingImage。
- 旧后端接口不需要改动。

## 验证方案

- 前端构建：`npm run build`
- 行为验证：
  - 选择图片后不应立即请求 `/api/meals`。
  - 点击确认后才请求 `/api/meals`。
  - 请求 payload 包含 image 和 description。
  - 失败后图片预览清空，描述保留。

## 预期结果

用户可以完整完成“选图 → 填写描述 → 确认识别”的流程，避免 AI 在用户输入描述前提前识别。