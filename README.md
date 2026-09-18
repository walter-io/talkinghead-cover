# workbuddy-talkinghead-cover · 口播赛博朋克封面生成

提供 **人物形象 + 标题 + 标签**，即可生成 WorkBuddy 品牌风格的赛博朋克/霓虹口播视频封面。

- 竖版 9:16（1472×2624）
- 青绿 `#28b894` + 紫 `#6c4dff` 霓虹放射背景
- 居中 Q 版卡通人物
- 顶部白字黑描边大标题（6° 左低右高）
- 人物两侧青绿→紫渐变圆角标签牌

---

## 一、怎么用（对话里直接说）

最简单的用法：直接把三样东西丢给 WorkBuddy。

```
用我的形象 <图片路径> 做一张口播赛博朋克封面
标题：WorkBuddy 自动签到
标签：自动签到、多账号管理、积分管理、token统计
```

其他可用的说法：

| 你想要 | 这么说 |
|---|---|
| 换标题重出图 | 「用同一套风格，标题改成 WorkBuddy 多账号管理」 |
| 换标签 | 「标签改成：自动签到、积分管理」 |
| 微调位置 | 「积分管理和 token统计 两个标签再往上一点」 |
| 放大标题 | 「标题字号再大一点」 |

**你需要准备的只有三样**：

1. **人物形象** — 一张照片或已有卡通形象的图片路径（真人照片会自动 Q 版化）
2. **标题** — 两行，英文 + 中文；只给一整串（如「workbuddy自动签到」）会自动拆行
3. **标签** — 2~4 个短词

---

## 二、文件结构

```
workbuddy-talkinghead-cover/
├── SKILL.md                        # 技能主文档：视觉规范 + 执行流程（AI 主要读这个）
├── README.md                       # 本文件：使用说明
├── scripts/
│   ├── agnes_img2img.cjs           # 第 1 步：调 Agnes 生成底图
│   └── compose_cover.py            # 第 2 步：叠加标题 + 标签
├── assets/fonts/
│   └── ZCOOLKuaiLe-Regular.ttf     # 内置中文漫画字体（站酷快乐体）
└── examples/
    ├── agnes-config.example.json   # Agnes 配置示例
    └── cover-config.example.json   # 合成配置示例
```

---

## 三、手动执行（不走对话）

### 前置：Agnes API Key

两种任选其一：

- 环境变量 `AGNES_API_KEY`
- 或纯文本文件 `C:\Users\we\.agnes_key`（脚本会自动回退读取）

### 第 1 步：Agnes 生成底图

复制 `examples/agnes-config.example.json` 改好内容：

```json
{
  "image": "C:/path/to/你的形象图.png",
  "prompt": "参考这张人物图片，把它转换成 Q 版卡通形象……（保持模板，替换人物特征描述）",
  "out": "C:/Users/we/agnes-output/wb-cover-base.png",
  "model": "agnes-image-2.1-flash",
  "size": "2K",
  "ratio": "9:16"
}
```

运行：

```bash
node scripts/agnes_img2img.cjs agnes-config.json
```

**生成后务必查看底图**：人物是否完整、顶部 1/3 是否留空、有没有冒出文字。不满足就改 prompt 重跑。

### 第 2 步：叠加标题 + 标签

复制 `examples/cover-config.example.json` 改好内容：

```json
{
  "base": "C:/Users/we/agnes-output/wb-cover-base.png",
  "out": "C:/Users/we/agnes-output/cover.png",
  "title": { "line1": "WorkBuddy", "line2": "自动签到" },
  "labels": [
    { "text": "自动签到",   "fx": 0.215, "fy": 0.505, "size": 112 },
    { "text": "多账号管理", "fx": 0.792, "fy": 0.548, "size": 102 },
    { "text": "积分管理",   "fx": 0.215, "fy": 0.660, "size": 112 },
    { "text": "token统计",  "fx": 0.792, "fy": 0.700, "size": 102 }
  ],
  "title_top": 0.032,
  "title_line_gap": 115,
  "title_angle": 6
}
```

运行：

```bash
python scripts/compose_cover.py cover-config.json
```

依赖：Python + Pillow（`pip install pillow`）。字体已内置，无需另装。

---

## 四、参数说明

### Agnes 配置（agnes-config.example.json）

| 字段 | 必填 | 说明 |
|---|---|---|
| `image` | 否 | 人物形象图路径。给了就是图生图；不给则纯文生图 |
| `prompt` | ✅ | 生图提示词，用模板替换人物特征即可 |
| `out` | ✅ | 底图输出路径 |
| `model` | 否 | 默认 `agnes-image-2.1-flash` |
| `size` | 否 | 默认 `2K` |
| `ratio` | 否 | 默认 `9:16` |

### 合成配置（cover-config.example.json）

| 字段 | 默认 | 说明 |
|---|---|---|
| `base` / `out` | — | 底图路径 / 输出路径 |
| `title.line1` / `line2` | — | 标题两行（英文 / 中文） |
| `labels[].text` | — | 标签文字 |
| `labels[].fx` / `fy` | — | 标签中心位置（相对宽高的比例 0~1） |
| `labels[].size` | 110 | 标签字号 |
| `title_top` | 0.032 | 标题块距顶部比例（越大越往下） |
| `title_line_gap` | 115 | 标题两行间距（px） |
| `title_angle` | 6 | 标题倾斜角（度，正值左低右高） |
| `title_en_size` | 250 | 英文标题字号 |
| `title_cn_size` | 245 | 中文标题字号 |

### 标签位置参考（4 个标签）

已调好的默认坐标，直接照抄即可：

| 标签 | fx | fy |
|---|---|---|
| 第 1 个（左） | 0.215 | 0.505 |
| 第 2 个（右） | 0.792 | 0.548 |
| 第 3 个（左） | 0.215 | 0.660 |
| 第 4 个（右） | 0.792 | 0.700 |

少于 4 个标签时，在 `fy` 0.50 ~ 0.70 之间均匀分布、左右交替。

---

## 五、两条硬性规则

1. **中文文字绝不用 Agnes 渲染。**
   实测 Agnes 会把「多账号管理」写成「多帐号管理」、「token统计」错成「toten定计」。
   → Agnes 只负责生成**无文字的底图**，所有文字一律用字体精确叠加。

2. **Agnes 图生图会让画面元素整体位移**（实测人物被上移/重排 4~9%）。
   → 凡「某个元素必须纹丝不动」的需求，不能用全图 Agnes 重绘，只能做像素级局部编辑。

其他注意事项：

- 顶部 1/3 必须留空，否则标题会压住顶部元素。
- 标签居中定位时不要超出画布：左标签 `fx` ≥ 0.21，右标签 `fx` ≤ 0.80。
- 只调文字位置/字号时，**不必重新调 Agnes**，改合成配置重跑第 2 步即可（几秒钟出图）。

---

## 六、参考成品

- `C:\Users\we\agnes-output\cover-wb-autocheckin-v3.png` — 当前风格基准

---

## 七、常见问题

**Q：Agnes 生成的底图顶部有图标，标题压上去了？**
A：重跑第 1 步，并在 prompt 里强调「画面最顶部约三分之一的区域只保留干净的背景，不要放任何元素」。

**Q：中文出现了错别字？**
A：说明文字是 Agnes 画的。检查底图 prompt 里是否写了「不要出现任何文字、字母、数字」；文字必须全部由第 2 步的脚本叠加。

**Q：脚本报 `Unexpected UTF-8 BOM`？**
A：配置文件被写入了 BOM。脚本已兼容 `utf-8-sig` / 自动剥离 BOM；若仍报错，用纯 UTF-8 无 BOM 重新保存 JSON。

**Q：想换成深蓝黑 + 霓虹的纯正赛博朋克风？**
A：当前固化的实际配色是 WorkBuddy 青绿+紫霓虹。需要另一套深色预设时，改 `compose_cover.py` 里的 `TEAL` / `PURPLE` 常量并在 Agnes prompt 中更换背景描述即可。
