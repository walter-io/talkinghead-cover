---
name: workbuddy-talkinghead-cover
description: 生成口播赛博朋克封面 / WorkBuddy 品牌风格的 Q 版卡通口播封面（青绿 #28b894 + 紫色 #6c4dff 霓虹放射背景、居中 Q 版人物、顶部大标题、四周文字标签牌）。当用户提供「人物形象 + 标题 + 标签」并要求出封面图时使用；支持自媒体口播视频/图文封面、多标签功能展示封面。触发词：口播赛博朋克封面、赛博朋克口播封面、口播封面、赛博朋克封面、霓虹封面、封面、WorkBuddy 封面、生成封面图、做封面。
agent_created: true
---

# WorkBuddy 口播封面生成

用户在自媒体运营中会反复制作「同一风格、换标题/换标签」的口播封面。本技能把已定稿的视觉规范固化下来：用户只需提供 **人物形象图 + 标题文案 + 标签文案**，即可产出统一风格的封面。

## 视觉规范（已与用户确认，不要随意改动）

- 画布：竖版 **9:16**，输出 **1472×2624**（Agnes 2K 9:16）。
- 品牌色：青绿 `#28b894`、紫色 `#6c4dff`；背景为青绿→紫的放射状渐变光效，点缀紫色五角星。
- 人物：Q 版卡通，居中、全身、微笑，**画面上方约 1/3 留空**给标题。
- 标题：两行，第一行英文（`WorkBuddy`）+ 第二行中文；**白色填充 + 黑色描边**，字体 Comic Sans（英文）+ 站酷快乐体（中文），字号约 250 / 245，整体 **6° 左低右高倾斜**，贴顶部。
- 标签：圆角胶囊牌（青绿→紫对角渐变底 + 白色外描边），白色粗体中文，分左右两列排在人物两侧。
- 参考成品：`C:\Users\we\agnes-output\cover-wb-autocheckin-v3.png`。

## 关键经验（务必遵守）

1. **绝不要用 Agnes 渲染中文/文字。** 实测 Agnes 会把「多账号管理」写成「多帐号管理」、「token统计」错成「toten定计」。所有文字（标题 + 标签）一律用 PIL + 字体精确叠加。
2. **Agnes 只负责生成底图**（人物 + 背景 + 星星，**无任何文字、无图标面板**）。底图 prompt 里要显式声明「画面里不要出现任何文字、字母、数字」。
3. **Agnes 图生图会让画面元素整体位移**（实测人物会被上移/重排 4~9%）。因此凡「某元素必须纹丝不动」的需求都不能用全图 Agnes 重绘，只能做像素级局部编辑。
4. 顶部 1/3 一定要留空，否则标题会压住顶部元素。
5. 标签居中定位时注意不要超出画布：左标签 `fx` 建议 ≥ 0.21（宽 ~520px 时），右标签 `fx` ≤ 0.80。

## 输入

调用时向用户确认三样东西（缺什么问什么）：

1. **人物形象**：本地图片路径（真人照片或已有卡通形象均可）。
2. **标题**：两行，例如 `WorkBuddy` + `自动签到`；若用户只给一整串（如「workbuddy自动签到」），自动拆成英文行 + 中文行。
3. **标签**：2~4 个词，例如 `自动签到 / 多账号管理 / 积分管理 / token统计`。

## 执行流程

工作目录建议建在 `C:\Users\we\agnes-output\`（与历史产物一致）。

### 第 1 步：用 Agnes 生成底图

1. 写一个 Agnes 调用的 JSON 配置（见 `scripts/agnes_img2img.cjs` 顶部注释）：
   - `image`：人物形象图的路径（图生图输入）。
   - `prompt`：按下面模板填写（把人物描述替换成用户形象的特征）。
   - `out`：底图输出路径。
2. 运行：
   ```
   node <托管node> scripts/agnes_img2img.cjs config.json
   ```
   托管 node 路径见系统提示（`C:\Users\we\.workbuddy\binaries\node\versions\*\node.exe`）。
3. Agnes 的 key 从环境变量 `AGNES_API_KEY` 读取，读不到则回退到 `C:\Users\we\.agnes_key`（纯文本）。

底图 prompt 模板：

```
参考这张人物图片，把它转换成 Q 版卡通形象，并做成一张竖版封面底图：
中央是一个 Q 版卡通人物（保持参考图人物的性别、发型、服装、姿势特征：<在此填人物特征>），
背景是青绿色(#28b894)到紫色(#6c4dff)的放射状渐变光效，四周点缀一些紫色五角星。
重要要求：画面最顶部约三分之一的区域只保留干净的背景，不要放任何元素，方便叠加标题；
画面里不要出现任何文字、字母、数字，也不要出现任何图标或面板，保持背景干净；
人物居中、全身、比例协调。
```

生成后**读图检查**：人物是否完整、顶部是否留空、有没有冒出文字。不满足就调整 prompt 重跑。

### 第 2 步：用 PIL 叠加标题 + 标签

1. 写一个合成配置 JSON（见 `scripts/compose_cover.py` 顶部注释），字段：
   - `base` 底图路径、`out` 成品路径
   - `title.line1` / `title.line2`
   - `labels`：数组，每项 `{text, fx, fy, size}`（fx/fy 是相对画布宽高的中心坐标 0~1）
   - 可选 `title_top`(默认 0.032)、`title_line_gap`(默认 115)、`title_angle`(默认 6)
2. 运行：
   ```
   python scripts/compose_cover.py config.json
   ```
   用托管 Python（`C:\Users\we\.workbuddy\binaries\python\versions\*\python.exe`）。脚本依赖 Pillow（PIL）与 NumPy，若缺失先 `pip install pillow numpy` 到托管环境的 venv。

### 第 3 步：交付

用 `present_files` 打开成品 PNG。若用户要微调（标签上下位置、标题字号、配色），只改合成 JSON 里的数值重跑第 2 步即可（不必重新调 Agnes）。

## 默认标签排布（4 个标签时）

左右两列、上密下疏：

| 标签 | fx | fy |
|---|---|---|
| 第 1 个（左） | 0.215 | 0.505 |
| 第 2 个（右） | 0.792 | 0.548 |
| 第 3 个（左） | 0.215 | 0.660 |
| 第 4 个（右） | 0.792 | 0.700 |

少于 4 个标签时，均匀分布在 fy 0.50 ~ 0.70 之间、左右交替即可。

## 字体

- 英文：`C:\Windows\Fonts\comic.ttf`（Comic Sans）。
- 中文：站酷快乐体 `ZCOOLKuaiLe-Regular.ttf`，优先取 `assets/fonts/`，其次 `C:\Users\we\agnes-output\fonts\`；都没有则从 https://github.com/google/fonts/raw/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf 下载到 `assets/fonts/`。
