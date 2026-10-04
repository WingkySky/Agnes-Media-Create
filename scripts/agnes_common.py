#!/usr/bin/env python3
"""
Agnes - 统一公共模块
======================================
为 Agnes AI API 相关脚本提供通用工具函数，供所有图像 / 视频脚本复用。

包含以下核心能力：
  1. 自动加载项目目录中的 .env 文件
  2. 统一获取 API Key（--key > 环境变量 > .env）
  3. 构造 API 请求头与 JSON 请求发送
  4. 基于 requests 的统一文件下载（支持流下载 + 进度显示
  5. 输出路径管理（默认目录 + 时间戳命名）
  6. 参数校验辅助函数

所有图像脚本和视频脚本都应从本模块导入。
"""

import ipaddress
import os
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# ─── 1. .env 文件自动加载 ─────────────────────────────────────────────

def _locate_dotenv():
    """从脚本所在目录向上查找 .env 文件，返回 Path 或 None。"""
    try:
        start = Path(__file__).resolve().parent
    except NameError:
        start = Path.cwd()

    for directory in [start, *start.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_dotenv(override=False):
    """解析 .env 文件并把 KEY=VALUE 写入 os.environ。

    Args:
        override: True 时覆盖已存在的同名环境变量；默认 False，不覆盖显式 export 的变量
    Returns:
        Path | None: 若实际加载的文件路径
    """
    env_file = _locate_dotenv()
    if not env_file:
        return None
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if not key:
                    continue
                if override or key not in os.environ:
                    os.environ[key] = value
        return env_file
    except OSError:
        return None


# 模块被导入时自动执行一次 .env 加载（不覆盖显式 export 的变量）。
# 必须在读取 AGNES_BASE_URL 等环境配置之前完成。
_LOADED_ENV_FILE = load_dotenv(override=False)


# ─── 全局配置 ────────────────────────────────────────────────────────────

_DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
# 支持通过环境变量 / .env 覆盖 API 基础地址（与官方文档的 AGNES_BASE_URL 对齐）
DEFAULT_BASE_URL = os.environ.get("AGNES_BASE_URL", "").strip() or _DEFAULT_BASE_URL
DEFAULT_API_KEY_ENV = "AGNES_API_KEY"
PLATFORM_URL = "https://platform.agnes-ai.com"

# 统一 User-Agent，用于请求与下载
_USER_AGENT = "Mozilla/5.0 Agnes-CLI/1.0"

# 本项目根目录（scripts/ 的父目录），用作输出文件的默认落点，
# 避免被其他 agent 从外部目录调用时把文件散落到调用方项目中。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 默认输出根目录（始终相对于本项目，而非 cwd）
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "output"


# ─── 2. 统一 API Key 获取 ─────────────────────────────────────────

def get_api_key(args_key=None):
    """获取 API Key（--key 参数 > 环境变量 > .env 文件）。

    Args:
        args_key: 命令行 --key 参数（可为 None）
    Returns:
        str: API Key
    """
    key = args_key or os.environ.get(DEFAULT_API_KEY_ENV)
    if key:
        return key
    print("Error: API key not found.")
    print(f"  1. Set env var: export {DEFAULT_API_KEY_ENV}='your-key'")
    print(f"  2. Create a .env file in the project directory with {DEFAULT_API_KEY_ENV}=...")
    print(f"  3. Use --key flag: python <script>.py 'prompt' --key your-key")
    print(f"  4. Get a key from: {PLATFORM_URL}")
    sys.exit(1)


# ─── 3. HTTP 头构造与请求发送 ──────────────────────────────────────

# host 校验结果缓存（进程内），避免轮询时反复做 DNS 解析
_URL_HOST_VERDICT = {}


def _host_is_public(host):
    """判断 host（域名或 IP 字面量）是否全部解析到公网地址。"""
    if host in _URL_HOST_VERDICT:
        return _URL_HOST_VERDICT[host]
    ok = True
    for info in socket.getaddrinfo(host, None):
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            ok = False
            break
        # IPv4-mapped IPv6 按其映射的 IPv4 判断
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if (ip.is_loopback or ip.is_private or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            ok = False
            break
    _URL_HOST_VERDICT[host] = ok
    return ok


def validate_public_http_url(url, label="URL"):
    """服务端发起请求前的 URL 安全校验（SSRF 防护）。

    规则：仅允许 http/https；host 解析结果不得包含 localhost / 环回 /
    私有 / 保留地址。校验失败时打印原因并退出。
    """
    def _reject(reason):
        print(f"❌ {label} 校验失败，已拒绝请求：{reason}")
        print(f"   URL: {str(url)[:120]}")
        sys.exit(1)

    try:
        parts = urlsplit(url)
    except ValueError:
        _reject("URL 无法解析")
        return
    if parts.scheme not in ("http", "https"):
        _reject(f"仅允许 http/https 协议（收到: {parts.scheme or '无 scheme'}）")
    host = parts.hostname
    if not host:
        _reject("缺少 host")
        return
    try:
        if not _host_is_public(host):
            _reject(f"host {host} 指向本机 / 环回 / 私有 / 保留地址")
    except (socket.gaierror, OSError) as e:
        _reject(f"host {host} 无法解析（{e}）")


def build_headers(api_key, extra=None):
    """构造 Agnes API 的标准请求头。

    Args:
        api_key: API Key
        extra: 可选额外 header 字典
    Returns:
        dict
    """
    h = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def http_post_json(api_key, url, payload, timeout=120):
    """统一的 POST JSON 请求，失败时打印错误并退出。

    Returns:
        dict: 解析后的 JSON 响应
    """
    validate_public_http_url(url, label="请求 URL")
    try:
        response = requests.post(
            url,
            headers=build_headers(api_key),
            json=payload,
            timeout=timeout,
        )
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        sys.exit(1)

    if 200 <= response.status_code < 300:
        return response.json()

    print(f"❌ 请求失败: HTTP {response.status_code}")
    print(f"   Response: {response.text}")
    sys.exit(1)


def http_get_json(api_key, url, params=None, timeout=60):
    """统一的 GET JSON 请求，失败时返回 None 以便调用方重试。

    Returns:
        dict | None
    """
    validate_public_http_url(url, label="请求 URL")
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            params=params,
            timeout=timeout,
        )
        if 200 <= response.status_code < 300:
            return response.json()
        print(f"   ⚠️  HTTP {response.status_code}")
        return None
    except Exception as e:
        print(f"   ⚠️  异常: {e}")
        return None


# ─── 4. 统一文件下载（图片 / 视频通用） ────────────────────────

def download_file(file_url, output_path, label="文件"):
    """从 URL 下载任意二进制文件，带进度显示。

    Args:
        file_url: 文件 URL
        output_path: 保存路径（str / Path）
        label: 输出信息前缀（例如 "视频" / "图片"）
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    validate_public_http_url(file_url, label="下载 URL")

    try:
        print(f"\n📥 下载{label}到 {output} ...")
        with requests.get(file_url, stream=True, timeout=300,
                          headers={"User-Agent": _USER_AGENT}) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(output, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = int(downloaded * 100 / total)
                            print(f"   进度: {pct:>3}%  ({downloaded}/{total} bytes)",
                                  end="\r")
        print()
        size = output.stat().st_size
        size_mb = size / (1024 * 1024)
        if size_mb >= 1:
            print(f"✅ 已保存: {output}  ({size_mb:.2f} MB)")
        else:
            print(f"✅ 已保存: {output}  ({size} bytes)")
        return output
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print(f"   请手动访问: {file_url}")
        sys.exit(1)


# ─── 5. 输出路径管理 ───────────────────────────────────────────────

def make_output_path(user_output, default_dir, file_suffix=".png"):
    """统一输出路径生成。

    默认目录相对于本项目根目录（Agnes-Media-Create/）解析，而不是调用方的 cwd，
    这样即便被其他 agent 从外部项目目录调用，生成的文件也会落到本项目的 output/ 中。

    Args:
        user_output: 用户指定路径，None 表示使用默认目录 + 时间戳命名；
                     支持相对路径（相对于本项目根目录）或绝对路径
        default_dir: 默认输出目录（如 output/image/text-to-image），相对路径会
                     以本项目根目录为基准解析
        file_suffix: 文件后缀，默认 .png

    Returns:
        Path: 最终保存路径（绝对路径）
    """
    if user_output:
        # 用户显式指定路径：绝对路径直接使用，相对路径以本项目根目录为基准
        user_path = Path(user_output)
        if user_path.is_absolute():
            return user_path
        return (PROJECT_ROOT / user_path).resolve()

    # 默认路径：以本项目根目录为基准（而非 cwd），避免被其他 agent 调用时散落文件
    default_abs = Path(default_dir)
    if not default_abs.is_absolute():
        default_abs = (PROJECT_ROOT / default_dir).resolve()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return default_abs / f"{default_abs.name}_{timestamp}{file_suffix}"


# ─── 6. 参数校验辅助函数 ──────────────────────────────────────────────

def validate_in_range(name, value, lo, hi):
    """校验 value 是否在 [lo, hi] 范围内，否则退出。"""
    if value < lo or value > hi:
        print(f"❌ {name} ({value}) 必须在 {lo}-{hi} 范围内")
        sys.exit(1)
    return value


def validate_in_list(name, value, allowed):
    """校验 value 是否在 allowed 列表中，否则退出。"""
    if value not in allowed:
        print(f"❌ {name} ({value}) 必须是 {allowed} 之一")
        sys.exit(1)
    return value
