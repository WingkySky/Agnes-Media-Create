#!/usr/bin/env python3
"""
Agnes Video 2.5 / 2.5 Flash - 图生视频 / 关键帧 / 多模态参考
================================================================
支持两类 mode：
  - keyframe：首尾帧控制。至少提供 --first-frame 或 --last-frame 之一。
  - reference：多模态参考。提供 images / audios / videos 至少一类非空。
    提示词中使用 <Picture N> / <Audio N> / <Video N> 指代第 N 个素材（从 1 计数）。

注意：
  - 所有图片/音频/视频 URL 必须公网可访问，且在任务完成前保持有效。
  - Flash 模型（agnes-video-2.5-flash）限制：size 仅 720P、images 最多 5 张、不支持参考视频。

用法：
  # 首尾帧控制
  python agnes_image_to_video_25.py "人物自然转身走向窗边" --mode keyframe \
      --first-frame https://example.com/first.png --last-frame https://example.com/last.png

  # 图片参考（角色一致性）
  python agnes_image_to_video_25.py "以 <Picture 1> 的角色在花田奔跑" --mode reference \
      --image https://example.com/character.png

  # 图片 + 音频参考（按节奏设计动作）
  python agnes_image_to_video_25.py "按 <Audio 1> 节奏运动" --mode reference \
      --image https://example.com/subject.png --audio https://example.com/music.mp3

  # 视频参考（复用动作与镜头节奏）
  python agnes_image_to_video_25.py "参考 <Video 1> 改成月夜卧室" --mode reference \
      --video https://example.com/input.mp4 --video-start 35
"""

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agnes_common as ac  # noqa: E402
import agnes_video_v25_common as v25  # noqa: E402


def _is_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _require_url(label, value):
    if value and not _is_url(value):
        print(f"❌ {label} 必须是公网可访问的 http(s) URL：{value[:80]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Agnes Video 2.5 - 图生视频 / 关键帧 / 多模态参考",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""说明：
  mode=keyframe 至少需要 --first-frame / --last-frame 之一。
  mode=reference 至少需要 --image / --audio / --video 之一。
  提示词中以 <Picture N> / <Audio N> / <Video N> 引用第 N 个素材。

默认输出目录：{v25.OUTPUT_DIR_I2V25}/
""")

    parser.add_argument("prompt", help="文本提示词（reference 模式可用 <Picture N> 等引用素材）")
    parser.add_argument("--mode", required=True, choices=v25.SUPPORTED_V25_MODES[1:],
                        help="生成模式：keyframe（首尾帧）/ reference（多模态参考）")
    parser.add_argument("--output", "-o", help="输出视频路径")
    parser.add_argument("--key", "-k", help="API Key（或设置 AGNES_API_KEY 环境变量）")
    v25.add_v25_common_args(parser)

    # keyframe 模式参数
    parser.add_argument("--first-frame", help="首帧图片 URL（keyframe 模式）")
    parser.add_argument("--last-frame", help="尾帧图片 URL（keyframe 模式）")

    # reference 模式参数
    parser.add_argument("--image", "-i", action="append", default=None,
                        help="参考图片 URL（可重复，reference 模式；Flash 最多 5 张）")
    parser.add_argument("--audio", "-a", action="append", default=None,
                        help="参考音频 URL（可重复，reference 模式）")
    parser.add_argument("--video", "-v", action="append", default=None,
                        help="参考视频 URL（可重复，reference 模式；Flash 不支持）")
    parser.add_argument("--video-start", type=int, default=0,
                        help="参考视频起始秒数（对所有 --video 统一生效，默认 0）")
    parser.add_argument("--video-require-audio", action="store_true",
                        help="参考视频要求带音轨（对所有 --video 统一生效）")

    args = parser.parse_args()

    # 校验公共参数
    sec, sz, ar = v25.validate_v25_params(
        model=args.model, mode=args.mode,
        seconds=args.seconds, size=args.size, aspect_ratio=args.aspect_ratio,
    )

    api_key = ac.get_api_key(args.key)
    output_path = ac.make_output_path(args.output, v25.OUTPUT_DIR_I2V25, file_suffix=".mp4")

    # ── 模式专属校验与 payload 构造 ──
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "mode": args.mode,
        "seconds": sec,
        "size": sz,
        "aspect_ratio": ar,
    }
    if args.seed is not None:
        payload["seed"] = args.seed

    if args.mode == "keyframe":
        _require_url("--first-frame", args.first_frame)
        _require_url("--last-frame", args.last_frame)
        if not (args.first_frame or args.last_frame):
            print("❌ keyframe 模式至少需要 --first-frame 或 --last-frame 之一")
            sys.exit(1)
        if args.image or args.audio or args.video:
            print("❌ keyframe 模式不允许传入 images / audios / videos")
            sys.exit(1)
        if args.first_frame:
            payload["first_frame"] = args.first_frame
        if args.last_frame:
            payload["last_frame"] = args.last_frame
        mode_label = "关键帧（首尾帧控制）"

    else:  # reference
        images = args.image or []
        audios = args.audio or []
        videos = args.video or []
        for idx, u in enumerate(images, 1):
            _require_url(f"--image #{idx}", u)
        for idx, u in enumerate(audios, 1):
            _require_url(f"--audio #{idx}", u)
        for idx, u in enumerate(videos, 1):
            _require_url(f"--video #{idx}", u)

        if not (images or audios or videos):
            print("❌ reference 模式至少需要 --image / --audio / --video 之一")
            sys.exit(1)
        if args.first_frame or args.last_frame:
            print("❌ reference 模式不允许传入 first_frame / last_frame")
            sys.exit(1)

        # Flash 专属校验
        if args.model == v25.FLASH_VIDEO_V25_MODEL:
            if videos:
                print("❌ agnes-video-2.5-flash 不支持参考视频（videos）")
                sys.exit(1)
            if len(images) > v25.FLASH_MAX_IMAGES:
                print(f"❌ agnes-video-2.5-flash 的 images 最多 {v25.FLASH_MAX_IMAGES} 张"
                      f"（收到 {len(images)} 张）")
                sys.exit(1)

        if images:
            payload["images"] = images
        if audios:
            payload["audios"] = audios
        if videos:
            payload["videos"] = [
                {
                    "url": u,
                    "start_seconds": args.video_start,
                    "require_audio": args.video_require_audio,
                }
                for u in videos
            ]
        mode_label = "多模态参考（reference）"

    # ── 摘要与执行 ──
    print(f"🎬 图生视频任务（V2.5 {mode_label}）")
    print(f"   提示词: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print(f"   模型:   {args.model}")
    print(f"   时长:   {sec}s  尺寸: {sz}  画幅: {ar}")
    if args.mode == "keyframe":
        if args.first_frame:
            print(f"   首帧: {args.first_frame[:80]}")
        if args.last_frame:
            print(f"   尾帧: {args.last_frame[:80]}")
    else:
        print(f"   参考图: {len(images)} 张  参考音频: {len(audios)} 个  参考视频: {len(videos)} 个")
    print(f"   输出文件: {output_path}")
    print()

    v25.run_video_generation(
        api_key=api_key,
        payload=payload,
        output_path=output_path,
        poll_interval=args.poll_interval,
        max_wait_seconds=args.max_wait,
    )


if __name__ == "__main__":
    main()
