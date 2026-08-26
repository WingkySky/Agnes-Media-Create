#!/usr/bin/env python3
"""
Agnes Video 2.5 / 2.5 Flash - 文生视频（Text-to-Video, mode=text）
====================================================================
使用 mode=text 根据文本提示词生成视频。
支持 agnes-video-2.5 与 agnes-video-2.5-flash 两个模型。

用法：
    python agnes_text_to_video_25.py "雨夜都市中银色跑车缓缓驶过，霓虹倒映地面"
    python agnes_text_to_video_25.py "prompt" --model agnes-video-2.5-flash --seconds 8 --aspect-ratio 9:16
    python agnes_text_to_video_25.py "prompt" --size 2K --aspect-ratio 21:9 --output my.mp4
"""

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agnes_common as ac  # noqa: E402
import agnes_video_v25_common as v25  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Agnes Video 2.5 - 文生视频（mode=text）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""示例：
  # 基础用法（默认 agnes-video-2.5，5 秒，720P，16:9）
  python %(prog)s "雨夜都市中银色跑车缓缓驶过"

  # 使用 Flash 模型免费生成竖屏短视频
  python %(prog)s "三只猫在月光森林行进" --model agnes-video-2.5-flash --aspect-ratio 9:16

  # 2K 超宽屏
  python %(prog)s "未来城市航拍" --size 2K --aspect-ratio 21:9 --seconds 10

默认输出目录：{v25.OUTPUT_DIR_T2V25}/
""")

    parser.add_argument("prompt", help="文本提示词")
    parser.add_argument("--output", "-o", help="输出视频路径")
    parser.add_argument("--key", "-k", help="API Key（或设置 AGNES_API_KEY 环境变量）")
    v25.add_v25_common_args(parser)

    args = parser.parse_args()

    # 校验公共参数
    sec, sz, ar = v25.validate_v25_params(
        model=args.model, mode="text",
        seconds=args.seconds, size=args.size, aspect_ratio=args.aspect_ratio,
    )

    api_key = ac.get_api_key(args.key)
    output_path = ac.make_output_path(args.output, v25.OUTPUT_DIR_T2V25, file_suffix=".mp4")

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "mode": "text",
        "seconds": sec,
        "size": sz,
        "aspect_ratio": ar,
    }
    if args.seed is not None:
        payload["seed"] = args.seed

    print("🎬 文生视频任务（V2.5 mode=text）")
    print(f"   提示词: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print(f"   模型:   {args.model}")
    print(f"   时长:   {sec}s  尺寸: {sz}  画幅: {ar}")
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
