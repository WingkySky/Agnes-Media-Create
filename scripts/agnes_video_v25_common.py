#!/usr/bin/env python3
"""
Agnes Video 2.5 / 2.5 Flash - 视频生成公共模块
=========================================================
基于 Agnes Video 2.5 的 OpenAI Videos 兼容 API，提供：
  - POST /v1/videos  创建视频任务
  - GET  /agnesapi?video_id=xxx&model_name=xxx  轮询结果（V2.5 推荐，所有模式都带 model_name）
  - 提取 metadata.url 并下载
  - mode（text / keyframe / reference）与尺寸、画幅、时长的专用校验
  - Flash 专属约束（size 仅 720P / 参考图最多 5 张 / 不支持参考视频）

与 agnes_video_common.py（V2.0）的区别：
  V2.0 使用 num_frames / frame_rate / width / height / image；
  V2.5 使用 mode / seconds / size / aspect_ratio / first_frame / last_frame / images / audios / videos。
  两套参数互不相容，因此使用独立模块，互不干扰。

依赖：agnes_common（提供统一的 HTTP / 下载 / 路径 / API Key）
"""

import sys
import time

import agnes_common as ac  # noqa: E402

# ─── 视频 API 配置 ───────────────────────────────────────────────────

# 创建任务端点与 V2.0 一致
CREATE_VIDEO_ENDPOINT = f"{ac.DEFAULT_BASE_URL}/videos"
# 查询端点与 V2.0 一致；V2.5 要求所有模式都带 model_name
QUERY_BY_VIDEO_ID_ENDPOINT = "https://apihub.agnes-ai.com/agnesapi"

# 模型 ID
DEFAULT_VIDEO_V25_MODEL = "agnes-video-2.5"
FLASH_VIDEO_V25_MODEL = "agnes-video-2.5-flash"

# 支持的生成模式
SUPPORTED_V25_MODES = ["text", "keyframe", "reference"]

# 分辨率档位（size 必须为字符串档位，不可写像素值）
SUPPORTED_V25_SIZES = ["720P", "960P", "2K"]

# 画幅比例白名单
SUPPORTED_V25_ASPECT_RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]

# 时长（seconds 必须为字符串 "4"–"12"）
V25_DEFAULT_SECONDS = "5"
V25_SECONDS_MIN = 4
V25_SECONDS_MAX = 12

# Flash 专属约束
FLASH_MAX_IMAGES = 5

# 输出目录
OUTPUT_BASE_VIDEO = "output/video"
OUTPUT_DIR_T2V25 = f"{OUTPUT_BASE_VIDEO}/text-to-video-v25"
OUTPUT_DIR_I2V25 = f"{OUTPUT_BASE_VIDEO}/image-to-video-v25"


# ─── 参数校验 ───────────────────────────────────────────────────────

def validate_mode(mode):
    """校验 mode 是否为 text / keyframe / reference。"""
    return ac.validate_in_list("mode", mode, SUPPORTED_V25_MODES)


def validate_seconds(seconds):
    """校验 seconds 是否为 4–12 之间的字符串/整数，返回字符串形式。"""
    try:
        val = int(seconds)
    except (TypeError, ValueError):
        print(f"❌ seconds ({seconds}) 必须是 4–12 之间的整数（字符串也可）")
        sys.exit(1)
    if val < V25_SECONDS_MIN or val > V25_SECONDS_MAX:
        print(f"❌ seconds ({val}) 必须在 {V25_SECONDS_MIN}-{V25_SECONDS_MAX} 之间")
        sys.exit(1)
    return str(val)


def validate_size(model, size):
    """校验 size 档位；Flash 仅允许 720P。"""
    if model == FLASH_VIDEO_V25_MODEL and size != "720P":
        print(f"❌ {FLASH_VIDEO_V25_MODEL} 的 size 必须为 720P（收到: {size}）")
        sys.exit(1)
    return ac.validate_in_list("size", size, SUPPORTED_V25_SIZES)


def validate_aspect_ratio(aspect_ratio):
    """校验 aspect_ratio 是否在白名单内。"""
    return ac.validate_in_list("aspect_ratio", aspect_ratio, SUPPORTED_V25_ASPECT_RATIOS)


def validate_v25_params(model, mode, seconds, size, aspect_ratio):
    """一次性校验 V2.5 公共参数，全部通过后原样返回。"""
    validate_mode(mode)
    sec = validate_seconds(seconds)
    sz = validate_size(model, size)
    ar = validate_aspect_ratio(aspect_ratio)
    return sec, sz, ar


# ─── 创建视频任务 ─────────────────────────────────────────────────

def create_video_task(api_key, payload):
    """POST /v1/videos 创建视频生成任务。

    Returns:
        dict: 响应 JSON（至少包含 task_id / id / video_id）
    """
    print("🎬 创建视频任务 ...")
    parts = [
        f"模型: {payload.get('model')}",
        f"模式: {payload.get('mode')}",
    ]
    if payload.get("seconds"):
        parts.append(f"时长: {payload.get('seconds')}s")
    if payload.get("size"):
        parts.append(f"尺寸: {payload.get('size')}")
    if payload.get("aspect_ratio"):
        parts.append(f"画幅: {payload.get('aspect_ratio')}")
    print("   " + "  ".join(parts))

    data = ac.http_post_json(api_key, CREATE_VIDEO_ENDPOINT, payload, timeout=120)
    task_id = data.get("task_id") or data.get("id")
    video_id = data.get("video_id")
    print("✅ 任务已创建")
    print(f"   task_id:  {task_id}")
    print(f"   video_id: {video_id}")
    return data


# ─── 轮询视频结果 ─────────────────────────────────────────────────

def poll_video_result(api_key, video_id, model_name,
                      poll_interval=3, max_wait_seconds=600):
    """轮询直到任务完成，返回最终 JSON。

    V2.5 要求所有模式查询都带 model_name，因此此处固定传入。
    """
    url = QUERY_BY_VIDEO_ID_ENDPOINT
    params = {"video_id": video_id, "model_name": model_name}

    print(f"\n⏳ 轮询视频结果（间隔 {poll_interval}s，最长 {max_wait_seconds}s）...")
    start = time.time()
    last_status = None
    while True:
        elapsed = int(time.time() - start)
        if elapsed > max_wait_seconds:
            print(f"❌ 等待超时（> {max_wait_seconds}s），请稍后手动查询")
            sys.exit(1)

        data = ac.http_get_json(api_key, url, params=params, timeout=60)
        if not data:
            time.sleep(poll_interval)
            continue

        status = data.get("status", "unknown")
        progress = data.get("progress", 0)

        if status != last_status:
            last_status = status
            print(f"   [{elapsed:>4}s] status={status:<11} progress={progress}%")
        else:
            print(f"   [{elapsed:>4}s] status={status:<11} progress={progress}%", end="\r")

        if status == "completed":
            print()
            print("✅ 视频生成完成")
            return data
        if status == "failed":
            print()
            print("❌ 视频生成失败")
            err = (data.get("error") or {})
            err_msg = err.get("message") if isinstance(err, dict) else err
            print(f"   Error: {err_msg or '未知错误'}")
            sys.exit(1)

        time.sleep(poll_interval)


# ─── 提取 video URL ───────────────────────────────────────────────

def extract_video_url(result_data):
    """从 V2.5 响应中提取视频 URL（位于 metadata.url）。"""
    if isinstance(result_data, dict):
        meta = result_data.get("metadata")
        if isinstance(meta, dict) and meta.get("url"):
            return meta["url"]
        # 兼容可能的顶层字段
        for key in ("video_url", "url"):
            val = result_data.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
    print("❌ 响应中未找到可访问的视频 URL")
    print(f"   响应: {result_data}")
    sys.exit(1)


# ─── 统一流程入口 ───────────────────────────────────────────────────

def run_video_generation(api_key, payload, output_path,
                         poll_interval=3, max_wait_seconds=600):
    """创建任务 → 轮询 → 下载。"""
    created = create_video_task(api_key, payload)
    video_id = created.get("video_id")
    if not video_id:
        print("❌ 创建任务响应中缺少 video_id，无法轮询")
        sys.exit(1)

    result = poll_video_result(
        api_key,
        video_id=video_id,
        model_name=payload.get("model"),
        poll_interval=poll_interval,
        max_wait_seconds=max_wait_seconds,
    )

    video_url = extract_video_url(result)
    ac.download_file(video_url, output_path, label="视频")
    return result


# ─── 公共 CLI 参数注入 ───────────────────────────────────────────

def add_v25_common_args(p):
    """向 argparse 中添加 V2.5 视频公共参数（model/seconds/size/aspect-ratio/seed/轮询）。"""
    p.add_argument("--model", default=DEFAULT_VIDEO_V25_MODEL,
                   help=f"模型名称（默认：{DEFAULT_VIDEO_V25_MODEL}；Flash 版：{FLASH_VIDEO_V25_MODEL}）")
    p.add_argument("--seconds", default=V25_DEFAULT_SECONDS,
                   help=f"视频时长（字符串 {V25_SECONDS_MIN}-{V25_SECONDS_MAX}，默认 {V25_DEFAULT_SECONDS}）")
    p.add_argument("--size", default="720P",
                   help="分辨率档位：720P / 960P / 2K（Flash 仅支持 720P）")
    p.add_argument("--aspect-ratio", default="16:9",
                   help="画幅比例：21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16")
    p.add_argument("--seed", type=int, default=None, help="随机种子（可选，相同种子提高可复现性）")
    p.add_argument("--poll-interval", type=int, default=3, help="轮询间隔秒数（默认 3）")
    p.add_argument("--max-wait", type=int, default=600, help="最长等待秒数（默认 600）")
    return p
