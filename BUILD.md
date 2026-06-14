# MediaToolSuite Android 构建指南

将 Python/KivyMD 项目编译为独立 APK。

## 方法一：本地构建 (Windows/Linux + Buildozer)

### 环境要求

- **Linux** (推荐 Ubuntu 22.04+) 或 **WSL2** (Windows 上)
- Python 3.10+
- Docker (可选，推荐使用 docker 版 buildozer)

### 步骤

#### 1. 安装 Buildozer

```bash
# 在 Linux 或 WSL2 中:
pip install --user buildozer
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

#### 2. 进入项目目录并执行构建

```bash
cd MediaToolSuite-Android

# 首次构建：自动下载 Android SDK/NDK (耗时较长)
buildozer android debug

# 如果找不到 SDK，可以使用:
buildozer android debug --debug
```

#### 3. 获取 APK

构建成功后 APK 位于：
```
bin/mediatoolsuite-1.0.0-arm64-v8a-debug.apk
```

传到手机安装即可。

### 使用 Docker (推荐，省去环境配置)

```bash
# 在项目目录中:
docker run --interactive --tty --rm \
    --volume "$(pwd)":/home/user/hostcwd \
    --volume ~/.buildozer:/home/user/.buildozer \
    --volume ~/.gradle:/home/user/.gradle \
    --workdir /home/user/hostcwd \
    kivy/buildozer:latest \
    android debug
```

---

## 方法二：使用 GitHub Actions 云构建 (无需本地环境)

创建 `.github/workflows/build.yml`：

```yaml
name: Build APK
on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install --user buildozer
          sudo apt update
          sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
      - name: Build with Buildozer
        run: |
          buildozer android debug
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: MediaToolSuite-APK
          path: bin/*.apk
```

上传到 GitHub 仓库 → Actions 页 → 运行 workflow → 下载 APK。

---

## 方法三：使用 Google Colab (免费云构建)

1. 打开 https://colab.research.google.com
2. 运行以下代码：

```python
!pip install --user buildozer
!sudo apt update
!sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

import os
os.chdir('/content')
!git clone https://github.com/你的用户名/MediaToolSuite-Android.git  # 或上传代码

!cd MediaToolSuite-Android && buildozer android debug

from google.colab import files
!ls bin/*.apk
files.download('bin/mediatoolsuite-1.0.0-arm64-v8a-debug.apk')
```

---

## 首次构建注意事项

- **首次构建约 30~60 分钟**（下载 SDK/NDK + 编译 Python-for-Android）
- **后续构建约 5~15 分钟**
- APK 大小约 25~40MB（含 Python 运行环境 + Kivy + Pillow）
- 如果需要图标，放一个 `icon.png` (256x256) 在项目根目录

## 安装到手机

APK 传输方式：
1. `adb install bin/*.apk` (USB 连接)
2. 微信/QQ 文件传输
3. 网盘下载
4. `scp` 通过局域网

安装后给存储权限即可正常使用所有工具。
