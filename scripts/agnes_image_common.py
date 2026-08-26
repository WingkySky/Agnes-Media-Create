#!/usr/bin/env python3
"""
Agnes Image - 图片生成公共模块
===================================
提供图像生成 (Text-to-Image & Image-to-Image) 的专用逻辑：
  - POST /v1/images/generations 调用
  - 响应解析（URL / b64_json）
  - 图片本地文件读入 base64（用于 i2i）

依赖：agnes_common（提供统一的 HTTP / 下载 / 路径 / API Key）
"""

import base64
import sys
from pathlib import Path

import agnes_common as ac  # noqa: E402

# ─── 图片 API 配置 ─────────────────────────────────────────────────────

IMAGE_CREATE_ENDPOINT = f"{ac.DEFAULT_BASE_URL}/images/generations"

DEFAULT_IMAGE_MODEL = "agnes-image-2.1-flash"
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_QUALITY = "standard"

# 输出目录
OUTPUT_BASE_IMAGE = "output/image"
OUTPUT_DIR_T2I = f"{OUTPUT_BASE_IMAGE}/text-to-image"
OUTPUT_DIR_I2I = f"{OUTPUT_BASE_IMAGE}/image-to-image"


# ─── 图片本地文件读取 ──────────────────────────────────────────────

_IMAGE_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def encode_image_to_base64(image_path):
    """读取本地图片文件并返回 data:mime;base64,... 字符串。

    Args:
        image_path: 本地图片路径
    Returns:
        str: data:image/xxx;base64,xxxx
    """
    p = Path(image_path)
    if not p.is_file():
        print(f"❌ 找不到图片文件: {image_path}")
        sys.exit(1)
    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = p.suffix.lstrip(".").lower() or "png"
    mime = _IMAGE_MIME.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


# ─── 调用图像 API ───────────────────────────────────────────────────

def create_image_task(api_key, payload):
    """发起图像生成任务，返回原始 dict 响应。

    Args:
        api_key: API Key
        payload: 请求体（含 model / prompt / image / extra_body 等）

    Returns:
        dict: 响应 JSON（包含 data[0].url / data[0].b64_json）
    """
    print(f"🎨 发起图像生成请求（model={payload.get('model')}）")
    data = ac.http_post_json(api_key, IMAGE_CREATE_ENDPOINT, payload, timeout=120)

    # 简化的响应校验与打印
    if not data.get("data") or len(data["data"]) < 1:
        print(f"❌ 响应中没有 data 字段")
        print(f"   Response: {data}")
        sys.exit(1)
    return data


# ─── 响应解析与保存 ─────────────────────────────────────────────────

def extract_image_url(img_data):
    """从单条 data 中取出 URL 或 base64 数据。

    Returns:
        (kind, value):
            kind='url'   -> value=str URL
            kind='b64'   -> value=base64 字符串
    """
    b64 = img_data.get("b64_json") if isinstance(img_data, dict) else getattr(
        img_data, "b64_json", None)
    if b64:
        return "b64", b64
    url = img_data.get("url") if isinstance(img_data, dict) else getattr(
        img_data, "url", None)
    if url:
        return "url", url
    print(f"❌ 响应中未找到 url 或 b64_json")
    print(f"   data: {img_data}")
    sys.exit(1)


def save_image_response(img_data, output_path):
    """根据响应类型（URL / base64）保存图像。"""
    kind, value = extract_image_url(img_data)
    if kind == "b64":
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "wb") as f:
            f.write(base64.b64decode(value))
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"✅ 已保存 (base64): {output}  ({size_mb:.2f} MB)")
    else:
        ac.download_file(value, output_path, label="图片")


# ─── 文生图 / 图生图 的完整流程 ────────────────────────────────────

def run_text_to_image(api_key, model, prompt, size, quality, response_format, output_path):
    """文生图：一次请求 + 保存。"""
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }
    if response_format:
        payload["response_format"] = response_format

    print(f"🎨 文生图任务")
    print(f"   提示词: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"   model: {model}  size: {size}  quality: {quality}  format: {response_format or 'url'}")
    print(f"   输出: {output_path}")
    print()

    data = create_image_task(api_key, payload)
    save_image_response(data["data"][0], output_path)
    return data


def run_image_to_image(api_key, model, prompt, image_data, size, quality, response_format, output_path):
    """图生图：image_data 是 data URI（data:image/xxx;base64,...）或 URL。
    Agnes Image 2.1 Flash API 要求 image 放在 extra_body.image 数组中。"""
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
        "extra_body": {"image": [image_data]},
    }
    if response_format:
        payload["extra_body"]["response_format"] = response_format

    print(f"🎨 图生图任务")
    print(f"   提示词: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"   model: {model}  size: {size}  quality: {quality}")
    print(f"   输出: {output_path}")
    print()

    data = create_image_task(api_key, payload)
    save_image_response(data["data"][0], output_path)
    return data
