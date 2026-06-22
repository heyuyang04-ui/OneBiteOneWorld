# meal-photo-description-recognition 修复总结

## 本轮目标

新增“食物照片 + 用户文字描述”联合识别能力。用户上传照片时，可以补充描述这是什么食物、有哪些食材、口味偏好等信息，后端将描述和照片一起传给视觉大模型，提升识别准确率。

## 修改文件

### 后端

- `/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`

### 前端

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`

## 完成内容

### 1. 后端上传结构支持 description

`MealUpload` 从：

```py
class MealUpload(BaseModel):
    image: str
```

扩展为：

```py
class MealUpload(BaseModel):
    image: str
    description: Optional[str] = None
```

兼容旧请求，只传 `image` 不会 422。

### 2. 描述清洗与长度限制

在 `meals.py` 中新增：

```py
def _clean_description(value: str | None) -> str:
    return (value or "").strip()[:200]
```

后端会把用户描述截断到 200 字以内，避免异常长文本进入 prompt。

### 3. 描述进入视觉识别链路

`upload_meal()` 现在会传入：

```py
{
    "image": body.image,
    "mime_type": mime_type,
    "description": user_description,
}
```

并在识别结果中附加：

```py
recognition["user_description"] = user_description
```

这样后续 `meal_payload`、Agent event、主动通知上下文都可以拿到本次用户描述。

### 4. 视觉 prompt 支持图文联合识别

`vision_skill.py` 现在会把用户描述写入 prompt：

```text
用户补充描述：...
```

并要求模型：

- 同时参考图片和用户描述。
- 图片模糊/遮挡/外卖包装时，用用户描述补全菜名、食材和口味。
- 描述与图片冲突时，以图片为主。
- 不编造图片和描述都没有的信息。
- 图片不是食物时，不因为描述说是食物就强制判定为食物。

返回 JSON 增加：

```json
"description_used": true/false
```

异常 fallback 也会保留 `description_used`。

### 5. 首页增加食物描述输入

`Home.tsx` 新增状态：

```tsx
const [foodDescription, setFoodDescription] = useState('')
```

上传时发送：

```tsx
api.post('/meals', {
  image: base64,
  description: foodDescription.trim(),
})
```

页面“记录这一餐”区域新增 textarea：

```text
补充描述（可选）
例如：黄焖鸡米饭，加了土豆和青椒；或番茄牛腩面，少辣，多肉
```

限制 200 字并显示当前字数。

### 6. 样式适配

`Home.css` 新增 `.food-description-box` 样式，使用当前夜色/木质/琥珀主题：

- 暖色卡片背景。
- 木质边框。
- focus 时琥珀色高亮。
- 移动宽度下保持稳定展示。

## 验证结果

### 后端编译

命令：

```bash
python3 -m py_compile backend/models/schemas.py backend/routers/meals.py backend/skills/vision_skill.py
```

结果：通过。

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

说明：Vite 仍有原有 chunk size warning，不影响构建成功。

### 上传接口兼容性验证

后端重启后验证：

```text
image_only 200 True 图片识别服务暂时不可用，请稍后重试
with_description 200 True 图片识别服务暂时不可用，请稍后重试
long_description 200 True 图片识别服务暂时不可用，请稍后重试
```

结论：

- 只传 `image` 的旧流程兼容。
- 传 `image + description` 不会 422。
- 超长 description 请求也能被后端接收并截断处理。
- 当前视觉模型服务仍返回不可用兜底，但接口流程稳定，不会因新增字段失败。

## 当前服务

后端已重启，当前任务：

```text
2qtcov
```

前端 Vite 服务仍运行：

```text
http://localhost:5173/
```

## 任务状态

`.comate/specs/meal-photo-description-recognition/tasks.md` 中 6 个顶层任务均已完成。