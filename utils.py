"""
MediaToolSuite Android 版 - 共享工具函数
(从原 Tkinter 版适配)
"""
import os
import subprocess
from pathlib import Path

# ─── 文件格式常量 ───
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}


def get_image_files(path, recursive=False):
    """获取目录下的所有图片文件"""
    p = Path(path)
    if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
        return [p]
    pattern = "**/*" if recursive else "*"
    files = []
    for f in p.glob(pattern):
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            files.append(f)
    return sorted(files)


def format_size(bytes_val):
    """格式化文件大小"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / 1024 ** 2:.1f} MB"
    else:
        return f"{bytes_val / 1024 ** 3:.2f} GB"


def get_android_storage_path():
    """获取 Android 可访问的存储路径"""
    if os.name == "posix" and "ANDROID" in os.environ:
        return "/storage/emulated/0"
    return os.path.expanduser("~")


def get_downloads_path():
    """获取 Android 下载目录"""
    base = get_android_storage_path() if "ANDROID" in os.environ else os.path.expanduser("~")
    d = os.path.join(base, "Download" if "ANDROID" in os.environ else "Downloads")
    os.makedirs(d, exist_ok=True)
    return d


def get_pictures_path():
    """获取 Android 图片目录"""
    base = get_android_storage_path() if "ANDROID" in os.environ else os.path.expanduser("~")
    d = os.path.join(base, "Pictures" if "ANDROID" in os.environ else "Pictures")
    os.makedirs(d, exist_ok=True)
    return d


def get_documents_path():
    """获取文档目录"""
    base = get_android_storage_path() if "ANDROID" in os.environ else os.path.expanduser("~")
    d = os.path.join(base, "Documents" if "ANDROID" in os.environ else "Documents")
    os.makedirs(d, exist_ok=True)
    return d
