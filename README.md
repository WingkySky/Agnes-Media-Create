
# 🎨 Agnes Media Create

[![Stars](https://img.shields.io/github/stars/your-org/agnes-media-create?style=flat)](https://github.com/)
[![Forks](https://img.shields.io/github/forks/your-org/agnes-media-create?style=flat)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![Shell](https://img.shields.io/badge/-Shell-4EAA25?logo=gnu-bash&logoColor=white)
![Markdown](https://img.shields.io/badge/-Markdown-000000?logo=markdown&logoColor=white)

> **4 Generation Modes** | **2 API Integrations** | **7 Standalone Modules** | **Auto-Polling** | **Cross-Platform**

---

<div align="center">

**🌐 Language / 语言**

[**English**](README.md) | [中文](README_zh.md)

</div>

---

**A modular CLI toolkit for generating media content using the Agnes Image 2.1 Flash, Agnes Video V2.0, and Agnes Video 2.5 / 2.5 Flash APIs.**

This is not just a single script. It's a complete system featuring a three-layer architecture: common utilities (`.env` auto-loading, HTTP requests, file downloading, parameter validation), API-specific encapsulation (image & video endpoints with response parsing), and standalone function scripts (text-to-image, image-to-image, text-to-video V2.0, and image-to-video V2.0 with multi-image/keyframe animation; plus 2.5-series scripts for text-to-video and keyframe / multimodal-reference video generation).

Designed for developers who want clean, production-ready scripts that just work — with zero setup friction and no OpenAI SDK dependency.

---

## ✨ Features

### Currently Supported

| Mode                         | Description                                                                                  | Script                      |
| ---------------------------- | -------------------------------------------------------------------------------------------- | --------------------------- |
| 🖼️**Text-to-Image**  | Generate images from text prompts                                                            | `agnes_text_to_image.py`  |
| 🖼️**Image-to-Image** | Modify existing images based on prompts + input image                                        | `agnes_image_to_image.py` |
| 🎬**Text-to-Video**    | Generate videos from text prompts (async with auto-polling)                                  | `agnes_text_to_video.py`  |
| 🎬**Image-to-Video**   | Generate videos from input images — single image, multi-image, and keyframe animation modes | `agnes_image_to_video.py` |
| 🎬**Text-to-Video 2.5 (mode=text)** | Based on `agnes-video-2.5` / `agnes-video-2.5-flash`, by seconds / size tier / aspect ratio | `agnes_text_to_video_25.py` |
| 🎬**Keyframe 2.5 (mode=keyframe)** | First/last frame control (at least one) for precise start/end frames | `agnes_image_to_video_25.py` |
| 🎬**Multimodal Reference 2.5 (mode=reference)** | Reference images / audio / video; prompt uses `<Picture N>` / `<Audio N>` / `<Video N>` | `agnes_image_to_video_25.py` |

### Architecture Highlights

- **Three-layer modular design** — common foundation → API encapsulation → standalone scripts
- **`.env` auto-detection** — no manual export required, works from any subdirectory
- **Unified API key management** — CLI arg > environment variable > `.env` file
- **Async video polling** — intelligent wait with configurable interval and timeout
- **Validation-first** — video frame count (`8n+1` rule), frame rate, and URL format checked before sending
- **Zero heavy dependencies** — only `requests` needed; no OpenAI SDK lock-in

---

## 📦 Project Structure

```
agnes-media-create/
├── SKILL.md                              # Skill definition (frontmatter + usage guide)
├── README.md                             # Project documentation (English) — this file
├── README_zh.md                          # Project documentation (Chinese)
├── requirements.txt                      # Python dependencies
├── .env.example                          # Example environment variables
├── .env                                  # Optional: local API key config (auto-loaded)
├── scripts/
│   ├── agnes_common.py                   # Common utilities — .env / HTTP / download / paths
│   ├── agnes_image_common.py             # Image API encapsulation
│   ├── agnes_video_common.py             # Video V2.0 API encapsulation (async + polling)
│   ├── agnes_video_v25_common.py         # Video 2.5 / 2.5 Flash API encapsulation (mode / seconds / size / aspect_ratio)
│   ├── agnes_text_to_image.py            # Text-to-Image standalone script
│   ├── agnes_image_to_image.py           # Image-to-Image standalone script
│   ├── agnes_text_to_video.py            # Text-to-Video V2.0 standalone script
│   ├── agnes_image_to_video.py           # Image-to-Video V2.0 standalone script (multi-image / keyframes)
│   ├── agnes_text_to_video_25.py         # Text-to-Video 2.5 standalone script (mode=text)
│   └── agnes_image_to_video_25.py        # Keyframe / reference video 2.5 standalone script (mode=keyframe / reference)
└── output/
    ├── image/text-to-image/              # Text-to-Image outputs
    ├── image/image-to-image/             # Image-to-Image outputs
    ├── video/text-to-video/              # Text-to-Video V2.0 outputs
    ├── video/image-to-video/             # Image-to-Video V2.0 outputs
    ├── video/text-to-video-v25/          # Text-to-Video 2.5 outputs
    └── video/image-to-video-v25/         # Keyframe / reference video 2.5 outputs
```

---

## 🚀 Quick Start

Up and running in 2 minutes:

### Step 1: Install Dependencies

```bash
cd /path/to/Agnes-Media-Create
pip install -r requirements.txt
# Or minimal install:
# pip install requests
```

### Step 2: Configure API Key

Get your key from https://platform.agnes-ai.com, then:

```bash
# Option A — Use .env (Recommended — auto-detected, no export needed)
cp .env.example .env
# Edit .env and set AGNES_API_KEY=sk-your-key-here

# Option B — Environment variable
export AGNES_API_KEY='your-api-key'

# Option C — Pass via CLI argument
python scripts/agnes_text_to_image.py "prompt" --key 'your-api-key'
```

### Step 3: Generate Something

```bash
# 🖼️ Text-to-Image
python scripts/agnes_text_to_image.py "a futuristic city at sunset, cinematic lighting"

# 🖼️ Image-to-Image (auto-converts local files to base64)
python scripts/agnes_image_to_image.py "make it sunset style" -i input.jpg

# 🎬 Text-to-Video (auto-polls until complete)
python scripts/agnes_text_to_video.py "a swordsman running through neon-lit skyscrapers" \
    --num-frames 121 --frame-rate 24

# 🎬 Image-to-Video (single image / multi-image / keyframe animation modes)
python scripts/agnes_image_to_video.py "character slowly turning around" \
    --image https://example.com/portrait.png
```

✨ **That's it!** Outputs are saved to the `output/` directory with timestamp-based filenames.

---

## 📖 Complete Usage Reference

### Text-to-Image

```bash
python scripts/agnes_text_to_image.py "prompt" [OPTIONS]
```

| Flag              | Description                                 | Default                        |
| ----------------- | ------------------------------------------- | ------------------------------ |
| `--output, -o`  | Custom output file path                     | Auto-generated in category dir |
| `--model`       | Model name                                  | `agnes-image-2.1-flash`      |
| `--size, -s`    | Image size (e.g.`1024x1024`, `512x512`) | `1024x1024`                  |
| `--quality, -q` | Quality:`standard` or `hd`              | `standard`                   |
| `--format, -f`  | Response format:`url` or `b64`          | `url`                        |
| `--key, -k`     | API key (overrides env / .env)              | From env or `.env`           |

### Image-to-Image

```bash
python scripts/agnes_image_to_image.py "prompt" -i input.jpg [OPTIONS]
```

| Flag              | Description                                                             | Default                   |
| ----------------- | ----------------------------------------------------------------------- | ------------------------- |
| `--image, -i`   | Input image — local file path (auto-converted to base64) or public URL | **required**        |
| `--model`       | Model name                                                              | `agnes-image-2.1-flash` |
| `--size, -s`    | Output image size                                                       | `1024x1024`             |
| `--quality, -q` | Quality:`standard` or `hd`                                          | `standard`              |

### Text-to-Video

```bash
python scripts/agnes_text_to_video.py "prompt" [OPTIONS]
```

| Flag                | Description                                                            | Default  |
| ------------------- | ---------------------------------------------------------------------- | -------- |
| `--num-frames`    | Total frames — must satisfy `8n+1` (e.g. 33, 49, 81, 121, 241, 441) | `121`  |
| `--frame-rate`    | Frame rate (1–60)                                                     | `30`   |
| `--width`         | Video width in pixels                                                  | `1152` |
| `--height`        | Video height in pixels                                                 | `768`  |
| `--seed`          | Random seed for reproducibility                                        | Random   |
| `--poll-interval` | Seconds between polling requests                                       | `5`    |
| `--max-wait`      | Maximum wait time in seconds before timeout                            | `600`  |

**Approximate duration by frame count** (at 24 fps):

| num_frames | Duration |
| ---------- | -------- |
| 33         | ~1.4s    |
| 81         | ~3.4s    |
| 121        | ~5.0s    |
| 241        | ~10.0s   |
| 441        | ~18.4s   |

### Image-to-Video

```bash
python scripts/agnes_image_to_video.py "prompt" --image URL [OPTIONS]
```

Supports three input modes:

1. **Single image** — `--image https://example.com/portrait.png`
2. **Multiple images** — `--image URL1 --image URL2`
3. **Keyframe animation** — `--image URL1 --image URL2 --keyframes`

| Flag                       | Description                                                           | Default            |
| -------------------------- | --------------------------------------------------------------------- | ------------------ |
| `--image, -i`            | Publicly accessible image URL — can be repeated for multi-image mode | **required** |
| `--keyframes`            | Enable keyframe animation mode                                        | Off                |
| `--num-frames`           | Total frames (`8n+1` rule)                                          | `121`            |
| `--frame-rate`           | Frame rate (1–60)                                                    | `30`             |
| `--width` / `--height` | Video resolution                                                      | `1152 / 768`     |

> ⚠️ **Note:** Agnes Video API requires publicly accessible image URLs for image-to-video. Local file paths are not supported.

### Video 2.5 / 2.5 Flash (recommended new models)

`agnes-video-2.5` and `agnes-video-2.5-flash` share an OpenAI Videos-compatible interface using the `mode / seconds / size / aspect_ratio` parameter scheme, which is incompatible with V2.0 (`num_frames` / `frame_rate` / `width` / `height`).

```bash
# Text-to-Video (text)
python scripts/agnes_text_to_video_25.py "Future city aerial, neon and mist" \
    --model agnes-video-2.5 --seconds 10 --size 2K --aspect-ratio 21:9

# Keyframe control (keyframe)
python scripts/agnes_image_to_video_25.py "Character turns and walks to the window" --mode keyframe \
    --first-frame https://example.com/first.png --last-frame https://example.com/last.png

# Multimodal reference (reference): images / audio / video
python scripts/agnes_image_to_video_25.py "Run through the flower field as <Picture 1>" --mode reference \
    --image https://example.com/character.png
python scripts/agnes_image_to_video_25.py "Move to the rhythm of <Audio 1>" --mode reference \
    --image https://example.com/subject.png --audio https://example.com/music.mp3
python scripts/agnes_image_to_video_25.py "Change <Video 1> scene to a moonlit bedroom" --mode reference \
    --video https://example.com/input.mp4 --video-start 35
```

| Flag | Description | Default |
| --- | --- | --- |
| `--model` | `agnes-video-2.5` or `agnes-video-2.5-flash` | `agnes-video-2.5` |
| `--seconds` | Duration, string `"4"`–`"12"` | `5` |
| `--size` | Size tier `720P` / `960P` / `2K` (Flash only `720P`) | `720P` |
| `--aspect-ratio` | Aspect ratio `21:9` / `16:9` / `4:3` / `1:1` / `3:4` / `9:16` | `16:9` |
| `--mode` (image script) | `keyframe` (first/last frame) / `reference` (multimodal) | required |
| `--first-frame` / `--last-frame` | First/last frame image URL (keyframe, at least one) | none |
| `--image` / `--audio` / `--video` | Reference image / audio / video URL (reference, repeatable) | none |
| `--video-start` / `--video-require-audio` | Reference video start second (default 0) / require audio track | `0` / off |

> **Flash-specific constraints**: `size` only `720P`; `reference.images` max 5; `reference` does not support `videos`. Violations are rejected by the script directly (no task created, no charge). Flash is currently free during a promotional period.

> ⚠️ **Note:** All media URLs in `keyframe` / `reference` modes must be publicly accessible and remain valid until the task completes; `reference` prompts reference the Nth asset with `<Picture N>` / `<Audio N>` / `<Video N>` (1-indexed).

---

## 📋 API Details

### Image API

- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **Endpoint**: `POST /v1/images/generations`
- **Model**: `agnes-image-2.1-flash`
- **Auth**: Bearer token via `Authorization: Bearer $AGNES_API_KEY`
- **Format**: OpenAI-compatible API

### Video API

#### V2.0

- **Base URL**: `https://api.agnes-ai.com/v1/videos`
- **Model**: `agnes-video-v2.0`
- **Flow**:
  1. `POST /v1/videos/generations` → creates async task, returns `task_id` / `video_id`
  2. `GET /v1/videos/{video_id}` → polls for completion status
  3. Status progresses: `in_progress` → `completed`
  4. Download video from the returned URL
- **Auth**: Bearer token via `Authorization: Bearer $AGNES_API_KEY`

#### 2.5 / 2.5 Flash

- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **Models**: `agnes-video-2.5` / `agnes-video-2.5-flash`
- **Create**: `POST /v1/videos` → returns `task_id` / `id` / `video_id`, `status` is `queued`
- **Query**: `GET /agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5` (pass `model_name` for all modes)
- **Complete**: when `status=completed`, get the video URL from `metadata.url` and download; on `status=failed`, inspect `error.message`
- **Modes**: `text` (text-to-video) / `keyframe` (`first_frame` / `last_frame`) / `reference` (`images` / `audios` / `videos`, prompt references via `<Picture N>` / `<Audio N>` / `<Video N>`)
- **Auth**: Bearer token via `Authorization: Bearer $AGNES_API_KEY`

---

## 🛠️ Architecture Overview

```
agnes_text_to_image.py
agnes_image_to_image.py  }  Standalone function scripts (CLI layer)
agnes_text_to_video.py
agnes_image_to_video.py
agnes_text_to_video_25.py    }  Video 2.5 series scripts
agnes_image_to_video_25.py

         │
         ▼

agnes_image_common.py    }  API-specific encapsulation (Business logic layer)
agnes_video_common.py        (V2.0)
agnes_video_v25_common.py    (2.5 / 2.5 Flash)

         │
         ▼

agnes_common.py          }  Common utilities (Foundation layer)
```

- **Foundation (`agnes_common.py`)** — `.env` auto-loading, API key resolution, HTTP requests, file downloading, path management, parameter validation. Shared by all scripts.
- **Business logic (`agnes_image_common.py` / `agnes_video_common.py` / `agnes_video_v25_common.py`)** — Encapsulates image, video V2.0, and video 2.5 API call flows, response parsing, and parameter validation (V2.0 `8n+1` frame rule; V2.5 seconds / size / aspect_ratio / Flash constraints).
- **CLI layer (6 standalone scripts)** — Each script only parses command-line arguments and calls the corresponding business logic — one script, one job.

---

## 📝 Example Output

### Text-to-Video

```
🎬 Text-to-Video task
   Prompt: a young swordsman in flowing robes running through neon-lit skyscrapers, cinematic
   Expected duration: ~5.04 seconds (121 frames / 24 fps)
   Output file: output/video/text-to-video/t2v_20260607_161011.mp4

🎬 Creating video task...
   Model: agnes-video-v2.0  Resolution: 1152x768  Frames/fps: 121/24
✅ Task created
   task_id:  task_mTtvzZl6qaHTJQg7ifoWDysd6Jqa73gj
   video_id: video_bGl0ZWxsbTpjdXN0b21fbGxt...

⏳ Polling video results (interval 5s, max 600s)...
   [   0s] status=in_progress progress=30%
   [ 119s] status=completed   progress=100%

✅ Video generation complete

📥 Downloading video to output/video/text-to-video/t2v_20260607_161011.mp4...
✅ Saved to: output/video/text-to-video/t2v_20260607_161011.mp4  (2.19 MB)
```

### Text-to-Image

```
🎨 Creating image...
   Model: agnes-image-2.1-flash  Size: 1024x1024  Quality: standard
✅ Saved to: output/image/text-to-image/t2i_20260607_155007.png
```

---

## 📦 Supported Image Sizes

| Size          | Aspect       |
| ------------- | ------------ |
| `1024x1024` | Square       |
| `512x512`   | Small square |
| `1024x512`  | Landscape    |
| `512x1024`  | Portrait     |

---

## 💡 Notes

- **Project root**: `/Users/skywing/Documents/Agnes-Media-Create`
- **Video generation** is asynchronous — scripts automatically poll and wait, typically 1–3 minutes
- **Image-to-Video** input images must be **publicly accessible URLs** — local file uploads are not supported by the API
- It's recommended to store your API Key in a `.env` file to avoid leaking it in command history

---

## 📜 License

MIT
