# 口播赛博朋克封面生成

提供 **人物形象 + 标题 + 标签**，即可生成 WorkBuddy 品牌风格的赛博朋克/霓虹口播视频封面。

- 竖版 9:16（1472×2624）
- 青绿 `#28b894` + 紫 `#6c4dff` 霓虹放射背景
- 居中 Q 版卡通人物（推荐半身大头）
- 顶部大标题：**微软雅黑粗体**、白字黑描边、6° 左低右高；**重点词自动放大并变亮黄**
- 底图由 **Agnes 生成**（含环绕人物的科技感面板：数据看板/手机/云/火箭/AI 徽章等）

---

## 一、怎么用（对话里直接说）

最简单的用法：直接把三样东西丢给 agent，以 WorkBuddy 为例。

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
| 突出标题里的词 | 「标题里"鸡蛋""免费"这两个词大一点」 |
| 加点科技感 | 「加点科技感的小图标，别和标题重合」 |

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
│   ├── compose_cover.py            # 第 2 步：叠加标题 + 标签 + 装饰图标
│   └── verify_no_overlap.py        # 第 3 步：校验装饰图标有没有压到标题
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
  "model": "agnes-image-2.5-flash",
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

复制 `examples/cover-config.example.json` 改好内容。**下面是当前最新的推荐配置**（= v11 基准，实测可直接跑通）：

```json
{
  "base": "C:/Users/we/agnes-output/wb-cover-tech-base2.png",
  "out":  "C:/Users/we/agnes-output/cover.png",
  "cn_font": "yahei",
  "title": {
    "lines": [
      { "text": "我们这代的{鸡蛋}", "size": 215, "ow": 16 },
      { "text": "{免费}的token",   "size": 215, "ow": 16 }
    ]
  },
  "labels": [],
  "title_top": 0.055,
  "title_max_bottom": 0.295,
  "title_line_gap": 18,
  "title_angle": 6,
  "title_emph_ratio": 1.28,
  "title_emph_color": "FFD400",
  "title_safe_margin": 0.028,
  "decor": { "enable": false }
}
```

> `size` 填 215 只是起点，脚本会按宽度/高度上限**自动收敛**（实测压到 165）。
> `decor.enable: false` 是因为底图里已经有 Agnes 画的环绕式科技面板；用纯背景底图时才开。

运行：

```bash
python scripts/compose_cover.py cover-config.json
```

依赖：Python + Pillow（`pip install pillow`）。字体用系统自带的微软雅黑，无需另装。

---

## 四、参数说明

### Agnes 配置（agnes-config.example.json）

| 字段 | 必填 | 说明 |
|---|---|---|
| `image` | 否 | 人物形象图路径。给了就是图生图；不给则纯文生图 |
| `prompt` | ✅ | 生图提示词，用模板替换人物特征即可 |
| `out` | ✅ | 底图输出路径 |
| `model` | 否 | 默认 `agnes-image-2.5-flash` |
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
| `labels[].icon` | 自动 | 标签左侧小图标，`false` 表示不加；可选 gift/coin/star/bolt/paw/rocket/code/phone/heart/sparkle |
| `title_top` | 0.032 | 标题块距顶部比例（越大越往下） |
| `title_line_gap` | 115 | 标题两行间距（px） |
| `title_angle` | 6 | 标题倾斜角（度，正值左低右高） |
| `title_en_size` | 250 | 英文标题字号 |
| `title_cn_size` | 245 | 中文标题字号 |
| `title_emph_ratio` | 1.28 | 标题里 `{强调词}` 的放大倍数 |
| `title_emph_color` | FFD400 | `{强调词}` 的填充色（亮黄，与白字形成层级）；可写 `"FF3D71"` 或 `[255,61,113]` |
| `cn_font` | yahei | 中文字体。可选 `yahei`(微软雅黑粗体) / `yahei_r`(雅黑常规) / `zcool`(站酷快乐体) / `simhei`(黑体) / `deng`(等线粗)；也可直接写字体文件名 |
| `title_safe_margin` | 0.035 | 标题左右安全边距，保证文字不超出画布 |
| `title_max_bottom` | — | 标题块底部上限（如 0.295），超限自动缩字号，保证不压到人物 |
| `decor.enable` | false | 是否叠加科技感装饰图标 |
| `decor.avoid_title` | true | 自动避让标题（保证不重合） |
| `decor.items[].icon` | spark | 装饰图标名：chip/bolt/signal/hex/gear/spark/atom/globe/code |
| `decor.items[].fx` / `fy` | — | 装饰图标中心位置（比例 0~1） |
| `decor.items[].size` | 0.05 | 小于 1 视为画面高度比例，大于 1 视为像素 |
| `decor.items[].rotate` | 0 | 旋转角度 |
| `decor.items[].alpha` | 150 | 透明度 0~255（科技图标建议 130~170） |

**标题强调词写法**：想放大标题里的某个词，用花括号圈起来：

```json
"title": { "line1": "我们这代的{鸡蛋}", "line2": "{免费}的token" }
```

效果：`{}` 内的字会**放大 1.28 倍**（`title_emph_ratio` 可调）并变成**鲜艳色**（`title_emph_color`，默认亮黄 `FFD400`），**与原文字基线对齐**、同行混排，不会一高一低。

想换强调色：

```json
"title_emph_color": "FF3D71"     // 玫红
"title_emph_color": "00E5FF"     // 电光青
"title_emph_color": [255, 212, 0] // 也可用数组
```

**科技感装饰图标位置参考**（本模板实测的安全区，避开标题带 13.5%~39.3%）：

| 位置 | fx | fy |
|---|---|---|
| 顶部左右角 | 0.062 / 0.938 | 0.040 |
| 标题下沿空白带 | 0.055 / 0.945 | 0.452 |
| 人物两侧上部 | 0.052 / 0.948 | 0.612 |
| 人物两侧下部 | 0.055 / 0.945 | 0.792 |
| 底部左右角 | 0.075 / 0.930 | 0.945 |

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

### 另一条默认行为（无需提醒）

**底图一律用「Agnes图像生成」技能生成，这是默认动作，用户不用每次说「用 Agnes」。**

流程会自动走完：加载 `Agnes图像生成` 技能 → 生成底图 → PIL 叠加文字 → 像素校验 → 交付。

仅两种情况可跳过 Agnes：

- 用户明确说「不要动底图 / 只改文字」
- 复用自己的历史底图（如 `wb-cover-tech-base2.png`）只重排文字

其他注意事项：

- 顶部 1/3 必须留空，否则标题会压住顶部元素。
- 标签居中定位时不要超出画布：左标签 `fx` ≥ 0.21，右标签 `fx` ≤ 0.80。
- 只调文字位置/字号时，**不必重新调 Agnes**，改合成配置重跑第 2 步即可（几秒钟出图）。

---

## 六、参考成品

- `C:\Users\we\agnes-output\cover-wb-token-v11.png` — 当前最新基准（微软雅黑粗体 + 强调词亮黄 + 半身大头 + 环绕科技面板）
- `C:\Users\we\agnes-output\cover-wb-token-v10.png` — 雅黑字体、强调词白色版
- `C:\Users\we\agnes-output\cover-wb-token-v9.png` — 站酷快乐体版（同构图）
- `C:\Users\we\agnes-output\cover-wb-egg-token-v5.png` — 全身版 + 6 标签 + 装饰图标
- `C:\Users\we\agnes-output\cover-wb-autocheckin-v3.png` — 半身 + 4 标签

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

**Q：加完装饰图标后，怎么确认没和标题重合？**
A：跑一次校验脚本，只看 `overlap` 是否为 0：

```bash
python scripts/verify_no_overlap.py 新成品.png 上一版成品.png 原始底图.png
```

输出 `VERDICT: PASS (无重合)` 即合格；若为 `FAIL`，说明某个装饰图标的 `fy` 落在了标题带里，把它挪到 0.04 / 0.45 / 0.61 / 0.79 / 0.945 这几个安全值上。

**Q：装饰图标全挤到同一行了？**
A：因为它们的 `fy` 都落在标题区间内（本模板标题实际占 13.5%~39.3%），避让逻辑会统一把它们推到标题下沿。把 `fy` 改到标题外的安全区即可。

**Q：想换字体？**
A：配置里加 `"cn_font": "..."`，默认是**微软雅黑粗体**（`yahei`）：

| 值 | 字体 |
|---|---|
| `yahei` | 微软雅黑 粗体（默认，正规清晰） |
| `yahei_r` | 微软雅黑 常规 |
| `zcool` | 站酷快乐体（手写卡通感） |
| `simhei` | 黑体 |
| `deng` | 等线 粗体 |

换字体后**不用手动调字号**——脚本会按宽度和高度上限自动重新收敛（雅黑比站酷体宽约 10%，同文案下字号会自动变小）。

**Q：日志里显示落位 x 21-1451，是不是切边了？**
A：不一定。日志打印的是**标题层外框**（含描边余量），比真实文字宽。以像素校验脚本输出的 `cols` 为准（实测外框 x21-1451，真实文字 x88-1366，留白充足）。

**Q：重点词想换个更鲜艳的颜色？**
A：改 `title_emph_color` 即可（`{}` 内的词会用它上色，其余保持白色）：

| 颜色 | 值 | 适用 |
|---|---|---|
| 亮黄（默认） | `FFD400` | 青绿紫背景上最醒目 |
| 玫红 | `FF3D71` | 想更抓眼、偏促销感 |
| 电光青 | `00E5FF` | 科技感更强 |
| 橙 | `FF7A00` | 暖色调画面 |

注意：**别选和背景同色系的颜色**（比如在橙黄背景上用橙黄字会糊在一起）。
