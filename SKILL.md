---
name: agnes-media-create
description: 通过 Agnes Image 2.1 Flash API 进行文生图和图生图；通过 Agnes Video V2.0 API 进行文生视频和图生视频；通过 Agnes Video 2.5 / 2.5 Flash API 进行文生视频、首尾帧控制（keyframe）与多模态参考（reference：图片/音频/视频）。当用户要求生成图片、视频，或根据描述创作/修改媒体内容时调用。
license: MIT
tags: ["agnes", "media-create", "image-generation", "video-generation", "text-to-image", "image-to-image", "text-to-video", "image-to-video", "ai-art", "creative-content"]
---

# Agnes Media Create 媒体生成技能

本 Skill 基于 `Agnes Image 2.1 Flash`、`Agnes Video V2.0` 与 `Agnes Video 2.5 / 2.5 Flash` API 提供以下功能：

- **文生图（Text-to-Image）**：根据文本描述生成图片
- **图生图（Image-to-Image）**：根据输入图片与文本提示词修改现有图片
- **文生视频 V2.0（Text-to-Video）**：根据文本描述生成视频（num_frames / frame_rate / 分辨率像素）
- **图生视频 V2.0（Image-to-Video）**：根据输入图片与文本提示词生成视频，支持多图/关键帧动画模式
- **文生视频 2.5（Text-to-Video, mode=text）**：基于 `agnes-video-2.5` / `agnes-video-2.5-flash`，按秒数、分辨率档位与画幅生成视频
- **首尾帧控制 2.5（mode=keyframe）**：提供首帧 / 尾帧（至少其一）精确控制视频起止画面
- **多模态参考 2.5（mode=reference）**：以图片 / 音频 / 视频作为参考，提示词中用 `<Picture N>` / `<Audio N>` / `<Video N>` 引用，保持角色一致性与运动/节奏对齐

> 模型版本说明：`Agnes Video 2.5` 与 `Agnes Video 2.5 Flash` 共用同一套 API（mode / seconds / size / aspect_ratio 参数体系），与 `Agnes Video V2.0`（num_frames / frame_rate / width / height 体系）互不兼容。新模型优先使用 2.5 系列脚本；V2.0 脚本保留以兼容旧调用。

**整个文件夹作为一个独立的 Skill 被智能体调用。**

## 项目结构（Skill 标准结构）

```
Skill 根目录/（整个文件夹作为 Skill 被调用）
├── SKILL.md                      # 本文件，Skill 定义（frontmatter + 使用说明）
├── README.md                     # 项目文档（英文）
├── README_zh.md                  # 项目文档（中文）
├── requirements.txt              # Python 依赖
├── .env.example                  # 环境变量示例
├── .env                          # 可选：本地 API Key 配置文件（无需 export 自动加载）
├── scripts/
│   ├── agnes_common.py           # 通用模块（.env 加载 / HTTP / 下载 / 路径）
│   ├── agnes_image_common.py     # 图片 API 封装
│   ├── agnes_video_common.py     # 视频 V2.0 API 封装（异步任务 + 轮询）
│   ├── agnes_video_v25_common.py # 视频 2.5 / 2.5 Flash API 封装（mode / seconds / size / aspect_ratio）
│   ├── agnes_text_to_image.py    # 文生图独立脚本
│   ├── agnes_image_to_image.py   # 图生图独立脚本
│   ├── agnes_text_to_video.py    # 文生视频 V2.0 独立脚本
│   ├── agnes_image_to_video.py   # 图生视频 V2.0 独立脚本（支持多图/关键帧）
│   ├── agnes_text_to_video_25.py # 文生视频 2.5 独立脚本（mode=text）
│   └── agnes_image_to_video_25.py# 图生视频 2.5 独立脚本（mode=keyframe / reference）
└── output/
    ├── image/text-to-image/      # 文生图输出目录
    ├── image/image-to-image/     # 图生图输出目录
    ├── video/text-to-video/      # 文生视频 V2.0 输出目录
    ├── video/image-to-video/     # 图生视频 V2.0 输出目录
    ├── video/text-to-video-v25/  # 文生视频 2.5 输出目录
    └── video/image-to-video-v25/ # 图生/参考视频 2.5 输出目录
```

## 前置条件

### 1. 依赖安装

只需原生 Python 3.8+ 和 `requests` 包：

```bash
cd /Users/skywing/Documents/Agnes-Media-Create
pip install requests
# 或使用项目提供的依赖文件
pip install -r requirements.txt
```

### 2. API Key 配置

API Key 可在 https://platform.agnes-ai.com 获取。有三种方式配置：

**方式 A：使用 `.env` 文件（推荐）**

```bash
cp .env.example .env
# 编辑 .env，填入：
# AGNES_API_KEY=sk-your-key-here
```

脚本会自动从项目目录查找 `.env` 文件并加载，无需手动 `export`。

**方式 B：环境变量**

```bash
export AGNES_API_KEY='your-api-key'
```

**方式 C：命令行参数**

```bash
python scripts/agnes_text_to_image.py "提示词" --key 'your-api-key'
```

优先级：命令行参数 > 环境变量 > `.env` 文件。

## 功能模块说明

每个功能都是一个独立的 Python 脚本，各自专注一件事。

### 1. 文生图（Text-to-Image）

根据文本提示词生成图片。

**调用方式**：

```bash
python scripts/agnes_text_to_image.py "文本提示词"
```

**示例**：

```bash
# 基础用法
python scripts/agnes_text_to_image.py "一只坐在月球上的小猫，超现实主义风格"

# 指定输出路径
python scripts/agnes_text_to_image.py "可爱的小狗" -o custom/dog.png

# 自定义模型与尺寸
python scripts/agnes_text_to_image.py "山脉风景" --size 1024x512 --quality hd
```

### 2. 图生图（Image-to-Image）

根据输入图片和文本提示词修改现有图片。

**调用方式**：

```bash
python scripts/agnes_image_to_image.py "文本提示词" -i 输入图片路径
```

**示例**：

```bash
# 传入本地图片（自动转为 base64）
python scripts/agnes_image_to_image.py "改成日落风格" -i input.jpg

# 传入公开 URL
python scripts/agnes_image_to_image.py "把画变成油画风格" -i https://example.com/img.jpg
```

### 3. 文生视频（Text-to-Video）

根据文本提示词生成视频（异步任务，脚本自动轮询结果）。

**调用方式**：

```bash
python scripts/agnes_text_to_video.py "文本提示词"
```

**视频参数**：

- `--num-frames`：总帧数，必须满足 `8n+1`（例如 33、49、65、81、97、121、241、441），默认 121
- `--frame-rate`：帧率（1–60），默认 30
- `--width` / `--height`：视频分辨率，默认 1152x768

**示例**：

```bash
# 基础用法（约 5 秒短视频，121 帧 / 24 fps）
python scripts/agnes_text_to_video.py "一位身穿飘逸长袍的年轻剑客，在雨夜都市中穿行" \
    --num-frames 121 --frame-rate 24

# 约 10 秒视频，更高分辨率
python scripts/agnes_text_to_video.py "一只独角兽奔跑在彩虹山脉上" \
    --width 1280 --height 720 --num-frames 241 --frame-rate 24
```

### 4. 图生视频 / 多图视频 / 关键帧动画（Image-to-Video）

根据输入图片与文本提示词生成视频，支持三种输入模式：

- **单图**：`--image URL`
- **多图**：`--image URL1 --image URL2`
- **关键帧动画**：`--image URL1 --image URL2 --keyframes`

**调用方式**：

```bash
python scripts/agnes_image_to_video.py "文本提示词" --image 图片URL
```

**示例**：

```bash
# 单图 → 视频（图生视频）
python scripts/agnes_image_to_video.py "人物缓慢转身回望镜头" \
    --image https://example.com/portrait.png

# 多图 → 视频
python scripts/agnes_image_to_video.py "平滑变换" \
    --image https://example.com/a.png --image https://example.com/b.png

# 关键帧动画
python scripts/agnes_image_to_video.py "平滑过渡" \
    --image https://example.com/kf1.png --image https://example.com/kf2.png \
    --keyframes
```

> **注意**：Agnes Video API 的图生视频需要图片为**公网可访问的 URL**。如果传入本地路径，脚本会提示并退出。

## 视频 2.5 / 2.5 Flash 模型（推荐新模型）

`Agnes Video 2.5`（`agnes-video-2.5`）与 `Agnes Video 2.5 Flash`（`agnes-video-2.5-flash`）共用 OpenAI Videos 兼容接口，参数体系为 `mode / seconds / size / aspect_ratio`，与 V2.0 不兼容。

- 两个模型支持三种生成模式：`text`（文生视频）、`keyframe`（首尾帧控制）、`reference`（多模态参考：图片 / 音频 / 视频）
- 查询任务推荐使用 `video_id` + `model_name` 组合（所有模式都带 `model_name`）
- **Flash 专属约束**：`size` 仅支持 `"720P"`；`reference` 模式 `images` 最多 5 张；`reference` 模式不支持 `videos`（传入有效内容返回 HTTP 400）。校验失败不产生任务、不计费。
- Flash 当前限时免费（输出 `$0 / 秒`）

**调用方式总览**：

```bash
# 文生视频（text）
python scripts/agnes_text_to_video_25.py "雨夜都市中银色跑车缓缓驶过" \
    --model agnes-video-2.5 --seconds 5 --size 720P --aspect-ratio 16:9

# 首尾帧控制（keyframe）
python scripts/agnes_image_to_video_25.py "人物自然转身走向窗边" --mode keyframe \
    --first-frame https://example.com/first.png --last-frame https://example.com/last.png

# 图片参考（reference）
python scripts/agnes_image_to_video_25.py "以 <Picture 1> 的角色在花田奔跑" --mode reference \
    --image https://example.com/character.png

# 图片 + 音频参考（按节奏设计动作）
python scripts/agnes_image_to_video_25.py "按 <Audio 1> 节奏运动" --mode reference \
    --image https://example.com/subject.png --audio https://example.com/music.mp3

# 视频参考（复用动作与镜头节奏）
python scripts/agnes_image_to_video_25.py "参考 <Video 1> 改成月夜卧室" --mode reference \
    --video https://example.com/input.mp4 --video-start 35
```

### 视频 2.5 公共参数

| 参数 | 适用 | 说明 | 默认值 |
|------|------|------|--------|
| `--model` | 全部 2.5 | `agnes-video-2.5` 或 `agnes-video-2.5-flash` | `agnes-video-2.5` |
| `--seconds` | 全部 2.5 | 视频时长，字符串 `"4"`–`"12"` | `5` |
| `--size` | 全部 2.5 | 分辨率档位：`720P` / `960P` / `2K`（Flash 仅 `720P`） | `720P` |
| `--aspect-ratio` | 全部 2.5 | 画幅：`21:9` / `16:9` / `4:3` / `1:1` / `3:4` / `9:16` | `16:9` |
| `--seed` | 全部 2.5 | 随机种子（相同种子提高可复现性） | 无 |
| `--poll-interval` | 全部 2.5 | 轮询间隔秒数（文档建议 1–2 秒） | `3` |
| `--max-wait` | 全部 2.5 | 最长等待秒数 | `600` |

**画幅与输出像素对照**（size 仅决定分辨率档位，实际像素由 aspect_ratio 决定）：

| aspect_ratio | 720P 输出像素 | 960P / 2K 按比例放大 |
|--------------|---------------|----------------------|
| `21:9` | 1680×720 | 同比例 |
| `16:9` | 1280×720 | 同比例 |
| `4:3` | 960×720 | 同比例 |
| `1:1` | 720×720 | 同比例 |
| `3:4` | 720×960 | 同比例 |
| `9:16` | 720×1280 | 同比例 |

### 模式一：文生视频（mode=text）

`agnes_text_to_video_25.py`，纯文本生成视频，无需任何媒体输入。

```bash
python scripts/agnes_text_to_video_25.py "未来城市航拍，霓虹与雨雾" \
    --size 2K --aspect-ratio 21:9 --seconds 10

# 使用 Flash 模型免费生成竖屏短视频
python scripts/agnes_text_to_video_25.py "三只猫在月光森林行进" \
    --model agnes-video-2.5-flash --aspect-ratio 9:16
```

### 模式二：首尾帧控制（mode=keyframe）

`agnes_image_to_video_25.py --mode keyframe`，至少提供 `--first-frame` 或 `--last-frame` 之一；不可同时传入 `images` / `audios` / `videos`。

```bash
python scripts/agnes_image_to_video_25.py "人物从首帧姿态自然转身走向窗边" --mode keyframe \
    --first-frame https://example.com/first.png \
    --last-frame https://example.com/last.png \
    --seconds 5 --size 720P
```

### 模式三：多模态参考（mode=reference）

`agnes_image_to_video_25.py --mode reference`，提供 `images` / `audios` / `videos` 至少一类非空；不可传入 `first_frame` / `last_frame`。

- 提示词中以 `<Picture N>` / `<Audio N>` / `<Video N>` 引用第 N 个素材（从 1 计数，按参数出现顺序）
- 参考视频用 `--video URL` 传入，可用 `--video-start`（起始秒，默认 0）与 `--video-require-audio`（要求原片带音轨）统一控制
- Flash 模型不支持 `videos`，且 `images` 最多 5 张

```bash
# 图片参考（角色一致性）
python scripts/agnes_image_to_video_25.py "以 <Picture 1> 的角色在花田奔跑，保持外观一致" \
    --mode reference --image https://example.com/character.png

# 图片 + 音频参考
python scripts/agnes_image_to_video_25.py "依 <Audio 1> 节奏设计动作与镜头切换" \
    --mode reference --image https://example.com/subject.png --audio https://example.com/music.mp3

# 视频参考（复用动作时序）
python scripts/agnes_image_to_video_25.py "参考 <Video 1> 的主体动作，把场景改为月夜卧室" \
    --mode reference --video https://example.com/input.mp4 --video-start 35

# Flash 图片参考（免费）
python scripts/agnes_image_to_video_25.py "以 <Picture 1> 风格生成角色奔跑" \
    --mode reference --model agnes-video-2.5-flash --image https://example.com/character.png
```

> **注意**：所有 `images` / `audios` / `videos` URL 必须公网可访问，且在任务完成前保持有效。Flash 模型下 `videos` 传参会直接被脚本拒绝（不会创建任务）。

## 常用参数总览

| 参数 | 适用范围 | 说明 | 默认值 |
|------|---------|------|--------|
| `prompt` | 全部 | 位置参数，文本提示词 | 必填 |
| `-o, --output` | 全部 | 输出文件路径 | 自动生成文件名（在对应分类目录） |
| `-k, --key` | 全部 | API Key | `AGNES_API_KEY` 环境变量 / `.env` |
| `--model` | 全部 | 模型名称 | 图片：`agnes-image-2.1-flash` / 视频 V2.0：`agnes-video-v2.0` / 视频 2.5：`agnes-video-2.5` 或 `agnes-video-2.5-flash` |
| `-s, --size` | 图片类 | 图片尺寸，例如 `1024x1024` | `1024x1024` |
| `-q, --quality` | 图片类 | 生成质量：`standard` / `hd` | `standard` |
| `-f, --format` | 图片类 | 响应格式：`url` / `b64` | `url` |
| `-i, --image` | 图生图/图生视频 | 输入图片（路径或 URL，视频脚本要求 URL） | 无 |
| `--num-frames` | 视频类 | 视频总帧数（需满足 `8n+1`） | `121` |
| `--frame-rate` | 视频类 | 帧率 1–60 | `30` |
| `--width / --height` | 视频类 | 视频分辨率 | `1152 / 768` |
| `--seed` | 视频类 | 随机种子（可选） | 无 |
| `--keyframes` | 图生视频 | 启用关键帧动画模式 | 关闭 |
| `--poll-interval` | 视频类 | 轮询间隔秒数 | `5` |
| `--max-wait` | 视频类 | 最长等待秒数 | `600` |
| `--seconds` | 视频 2.5 | 视频时长（字符串 `"4"`–`"12"`） | `5` |
| `--size` | 视频 2.5 | 分辨率档位 `720P` / `960P` / `2K`（Flash 仅 `720P`，与图片类的像素尺寸含义不同） | `720P` |
| `--aspect-ratio` | 视频 2.5 | 画幅 `21:9` / `16:9` / `4:3` / `1:1` / `3:4` / `9:16` | `16:9` |
| `--mode` | 视频 2.5 | `text` / `keyframe` / `reference`（文生视频脚本固定 `text`） | `text` / 必填 |
| `--first-frame` / `--last-frame` | 视频 2.5 keyframe | 首帧 / 尾帧图片 URL（至少其一） | 无 |
| `--image` / `--audio` / `--video` | 视频 2.5 reference | 参考图片 / 音频 / 视频 URL（可重复） | 无 |
| `--video-start` / `--video-require-audio` | 视频 2.5 reference | 参考视频起始秒（默认 0）/ 要求原片带音轨 | `0` / 关闭 |

> **脚本与模型对应关系**：`agnes_text_to_video.py` / `agnes_image_to_video.py` 仅用于 V2.0；`agnes_text_to_video_25.py` / `agnes_image_to_video_25.py` 仅用于 2.5 系列。两套参数互不相容，请勿混用。

## 支持的图片尺寸

- `1024x1024`（正方形）
- `512x512`（小正方形）
- `1024x512`（横向）
- `512x1024`（纵向）

## 视频帧数约束

视频 `num_frames` 必须满足 `8n + 1` 且 `≤ 441`。例如：

| n | num_frames | 大致时长 (24fps) |
|---|------------|------------------|
| 1 | 9 | 0.375s |
| 4 | 33 | 1.375s |
| 6 | 49 | 2.0s |
| 10 | 81 | 3.375s |
| 15 | 121 | 5.0s |
| 30 | 241 | 10.0s |
| 55 | 441 | 18.375s |

脚本会自动校验，不满足规则时会直接报错并给出推荐值。

## 输出目录结构

```
output/
├── image/
│   ├── text-to-image/          # 文生图输出
│   │   ├── t2i_20260607_155007.png
│   │   └── ...
│   └── image-to-image/         # 图生图输出
│       ├── i2i_20260607_155204.png
│       └── ...
└── video/
    ├── text-to-video/          # 文生视频 V2.0 输出
    │   ├── t2v_20260607_161011.mp4
    │   └── ...
    ├── image-to-video/         # 图生视频 V2.0 输出
    │   ├── i2v_20260607_161203.mp4
    │   └── ...
    ├── text-to-video-v25/      # 文生视频 2.5 输出
    │   ├── image-to-video-v25_20260826_210500.mp4
    │   └── ...
    └── image-to-video-v25/     # 首尾帧 / 多模态参考 2.5 输出
        ├── image-to-video-v25_20260826_210720.mp4
        └── ...
```

- 文件命名使用时间戳
- 使用 `-o` 或 `--output` 可自定义输出路径（跳过分类目录）

## 完整调用示例

### 场景 1：文生图

当用户说「帮我生成一张风景图」：

```bash
python scripts/agnes_text_to_image.py "雄伟的雪山风景，早晨阳光，油画风格"
```

### 场景 2：图生图

当用户说「把这张图片改成日落风格」：

```bash
python scripts/agnes_image_to_image.py "改成日落风格" -i /path/to/input.jpg
```

### 场景 3：文生视频

当用户说「生成一个剑侠在都市中穿行的视频」：

```bash
python scripts/agnes_text_to_video.py "一位身穿飘逸古风长袍的年轻剑客，在霓虹闪烁的现代都市摩天大楼之间奔跑穿梭，电影级宽银幕镜头" \
    --num-frames 121 --frame-rate 24 --width 1152 --height 768
```

### 场景 4：图生视频

当用户说「根据这张图片生成一段视频」：

```bash
python scripts/agnes_image_to_video.py "人物缓慢转身回望镜头" \
    --image https://your-storage.example.com/portrait.png
```

### 场景 5：文生视频（2.5 新模型）

当用户说「用新模型生成一段未来城市航拍视频」：

```bash
python scripts/agnes_text_to_video_25.py "未来城市航拍，霓虹与雨雾，电影级运镜" \
    --model agnes-video-2.5 --seconds 10 --size 2K --aspect-ratio 21:9
```

### 场景 6：首尾帧 / 多模态参考（2.5 新模型）

当用户说「用这两张图做首尾帧，让人物转身走到窗边」或「参考这张角色图生成奔跑视频」：

```bash
# 首尾帧控制
python scripts/agnes_image_to_video_25.py "人物自然转身走向窗边" --mode keyframe \
    --first-frame https://your-storage.example.com/first.png \
    --last-frame https://your-storage.example.com/last.png

# 图片参考（角色一致性）
python scripts/agnes_image_to_video_25.py "以 <Picture 1> 的角色在花田奔跑" \
    --mode reference --image https://your-storage.example.com/character.png
```

## 模块设计说明（供参考）

项目采用三层模块化设计，便于扩展与维护：

```
agnes_text_to_image.py
agnes_image_to_image.py  } 独立功能脚本（CLI 层）
agnes_text_to_video.py
agnes_image_to_video.py

         │
         ▼

agnes_image_common.py    } 专用 API 封装（业务逻辑层）
agnes_video_common.py

         │
         ▼

agnes_common.py          } 通用工具（底层基础层）
```

- **底层（`agnes_common.py`）**：`.env` 自动加载、API Key 获取、HTTP 请求、文件下载、路径管理、参数校验等所有脚本共享的基础功能。
- **业务逻辑层（`agnes_image_common.py` / `agnes_video_common.py`）**：分别封装图片和视频的 API 调用流程、响应解析、参数校验（如视频 `8n+1` 规则）。
- **CLI 层（四个独立脚本）**：仅负责解析命令行参数并调用对应业务逻辑，每个脚本只做一件事。

## 注意事项

- 项目根目录：`/Users/skywing/Documents/Agnes-Media-Create`
- 视频生成是**异步任务**，脚本会自动轮询等待，通常需要 1–3 分钟
- 图生视频（`image-to-video`）的输入图片必须是公网可访问的 URL，不支持本地文件直接上传
- **视频 2.5 / 2.5 Flash**：`keyframe` / `reference` 模式下的 `first_frame` / `last_frame` / `images` / `audios` / `videos` 全部要求公网可访问 URL，且在任务完成前保持有效；`reference` 模式提示词用 `<Picture N>` / `<Audio N>` / `<Video N>` 引用素材
- **视频 2.5 Flash 限制**：`size` 仅 `720P`、`reference.images` 最多 5 张、`reference` 不支持 `videos`；违反时脚本直接拒绝（不创建任务、不计费）
- 建议将 API Key 写入 `.env` 文件，避免在命令行中泄漏
