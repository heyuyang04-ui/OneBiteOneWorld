# meal-photo-description-recognition 需求说明

## 背景

当前用户上传食物照片后，后端只把图片传给视觉大模型进行识别。实际使用中，照片可能存在角度、光线、遮挡、复合菜、外卖包装等问题，导致模型识别不准确。用户希望新增一个输入，让用户描述“这是什么食物/里面有什么”，并将照片与描述一起传给大模型，提高识别准确性。

## 目标

在“记录这一餐”上传流程中支持：

- 用户上传食物照片。
- 用户可选填写食物描述，例如：
  - “这是外卖黄焖鸡米饭，加了土豆和青椒”
  - “番茄牛腩面，少辣，多肉”
  - “公司食堂的鸡胸肉沙拉，有玉米和鸡蛋”
- 前端提交 `{ image, description }`。
- 后端校验并截断描述，避免异常长文本。
- 后端把用户描述和图片一起传给视觉大模型。
- 大模型返回结构化餐食结果时优先结合用户描述，但仍保留图片校验能力。
- 返回结果中保留 `user_description`，供后续结果页和数据链路使用。

## 非目标

本轮不新增数据库字段，避免迁移影响已有数据。用户描述会进入：

- 视觉模型 prompt。
- 本次返回的 meal payload。
- orchestrator/proactive notification 数据上下文。

但不单独落库为 `meals.user_description` 字段。若后续需要长期保存原始用户描述，可单独做数据库迁移。

## 需求一：前端上传区增加食物描述输入

### 场景与处理逻辑

用户在首页“记录这一餐”区域，除了拍照/选图，还可以输入一段简短描述。描述是可选项：

- 不填写：继续使用原图片识别流程。
- 填写：随图片一起传给后端。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`：

- 增加状态：

```tsx
const [foodDescription, setFoodDescription] = useState('')
```

- 修改上传函数签名：

```tsx
const handleUpload = async (base64: string) => {
  const res = await api.post('/meals', {
    image: base64,
    description: foodDescription.trim(),
  })
}
```

- 在 `record-section` 中 `ImageUpload` 之前或之后增加 textarea：

```tsx
<textarea
  value={foodDescription}
  onChange={(e) => setFoodDescription(e.target.value)}
  maxLength={200}
  placeholder="可选：告诉 Agent 这是什么食物，例如：黄焖鸡米饭，加了土豆和青椒"
/>
```

- 上传失败时不清空描述，方便用户修改后重试。
- 上传成功跳转后无需清空，因为页面切换。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
- 如需样式：复用现有 inline style 或 `Home.css` 增加 `.food-description-input`。

## 需求二：后端上传 schema 支持 description

### 场景与处理逻辑

当前 `MealUpload` 只有：

```py
class MealUpload(BaseModel):
    image: str
```

需要增加可选描述字段。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`：

```py
class MealUpload(BaseModel):
    image: str
    description: Optional[str] = None
```

修改 `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`：

- 增加描述清洗函数：

```py
def _clean_description(value: str | None) -> str:
    text = (value or "").strip()
    return text[:200]
```

- 在 `upload_meal()` 中读取：

```py
user_description = _clean_description(body.description)
```

- 调用 `vision_skill` 时传入：

```py
recognition = await vision_skill(user_id, {
    "image": body.image,
    "mime_type": mime_type,
    "description": user_description,
})
```

- 在 `recognition` 和 `meal_payload` 中附加：

```py
recognition["user_description"] = user_description
```

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`

## 需求三：视觉模型 prompt 合并用户描述

### 场景与处理逻辑

当前 `vision_skill.py` prompt 只要求模型“分析这张食物照片”。需要把用户描述作为高优先级辅助信号，但不能让描述完全覆盖图片事实，避免用户误填导致错误。

### 技术方案

修改 `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`：

- 读取：

```py
user_description = (params.get("description") or "").strip()[:200]
```

- prompt 增加：

```text
用户补充描述：{user_description or "无"}

请同时参考图片和用户描述：
- 如果图片模糊或有遮挡，可以用用户描述补全菜名、食材、口味。
- 如果用户描述与图片明显冲突，以图片为主，并在 dish_name/ingredients 中选择更可信的信息。
- 不要编造描述中没有、图片也看不出的昂贵食材。
```

- JSON 返回要求中增加：

```json
"description_used": true/false
```

- 异常 fallback 中返回：

```py
"description_used": bool(user_description)
```

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vision_skill.py`

## 数据流

1. 用户在首页输入描述并上传照片。
2. `ImageUpload` 压缩图片并返回 base64。
3. `Home.tsx` 调用：

```ts
api.post('/meals', { image: base64, description: foodDescription.trim() })
```

4. `MealUpload` 接收 `image` 和 `description`。
5. `meals.py` 校验图片，清洗描述。
6. `vision_skill` 构造图文联合 prompt。
7. `AIClient.vision()` 将图片和 prompt 一起发给大模型。
8. 后端保存餐食记录、更新画像、生成 insight。
9. 前端跳转到 MealResult，展示结构化识别结果。

## 边界条件

- 描述为空：保持原逻辑。
- 描述超过 200 字：后端截断到 200 字，前端也设置 `maxLength=200`。
- 描述里有无关内容：prompt 要求模型以图片为主，描述只作为辅助。
- 图片不是食物但描述说是食物：仍应结合图片判断，不能仅凭描述强制 `is_food=true`。
- 图片服务异常：继续沿用当前稳定 fallback。

## 验证方案

- 后端编译：

```bash
python3 -m py_compile backend/models/schemas.py backend/routers/meals.py backend/skills/vision_skill.py
```

- 前端构建：

```bash
npm run build
```

- API smoke：
  - `POST /api/meals` 只传 image 能兼容旧流程。
  - `POST /api/meals` 传 image + description 能被后端接收，不产生 422。
  - 超长 description 被截断。

## 预期结果

- 用户可以用自然语言补充食物信息。
- 大模型能结合照片和描述识别，减少照片不清、复合菜、外卖包装导致的误识别。
- 旧上传流程保持兼容。
- 描述不会破坏图片校验和非食物判断。