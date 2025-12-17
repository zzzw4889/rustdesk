#!/usr/bin/env python3
"""
wtdesk 专用构建脚本（基于原 build.py 封装）

用法基本与原来的 build.py 一致，例如：
    python build2.py --flutter --hwcodec

脚本会：
1. 直接调用原始 build.py 完成正常构建；
2. 根据版本号，把最终输出的安装包/镜像文件从 rustdesk* 重命名为 wtdesk*；
   - Windows:  rustdesk-<ver>-install.exe / rustdesk-<ver>-win7-install.exe → wtdesk-...
   - Linux:    rustdesk-<ver>.deb / rustdesk-<ver>-*.rpm / *.pkg.tar.zst    → wtdesk-...
   - macOS:   rustdesk-<ver>.dmg → wtdesk-<ver>.dmg

注意：
- 本脚本只修改“对外可见的文件名”，不会动包内部的 service/desktop 名称和二进制内部名称；
- 如果你还需要改 crate 名称 / Flutter 工程名，请在对应工程里改。
"""

import importlib
import os
import platform
import sys
from pathlib import Path


def _try_rename(old: Path, new: Path):
    """安全重命名：存在才改，目标存在则先删除。"""
    try:
        if old.is_file():
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.exists():
                new.unlink()
            old.rename(new)
            print(f"[wtdesk] rename: {old} -> {new}")
    except Exception as e:
        print(f"[wtdesk] rename failed: {old} -> {new}: {e}")


def _rename_outputs_to_wtdesk(version: str):
    """
    根据当前平台，把根目录下的 rustdesk 产物重命名为 wtdesk。
    仅依赖最终文件名，不侵入原 build.py 逻辑。
    """
    root = Path(os.path.abspath(os.curdir))

    system = platform.system().lower()

    # 通用：根目录下的 deb / dmg / 其它包
    # deb (多种路径最终都会生成 rustdesk-<ver>.deb 在根目录)
    _try_rename(root / f"rustdesk-{version}.deb",
                root / f"wtdesk-{version}.deb")

    # Manjaro / Arch
    _try_rename(
        root / f"rustdesk-{version}-0-x86_64.pkg.tar.zst",
        root / f"wtdesk-{version}-0-x86_64.pkg.tar.zst",
    )
    _try_rename(
        root / f"rustdesk-{version}-manjaro-arch.pkg.tar.zst",
        root / f"wtdesk-{version}-manjaro-arch.pkg.tar.zst",
    )

    # Fedora / CentOS RPM
    _try_rename(
        root / f"rustdesk-{version}-0.x86_64.rpm",
        root / f"wtdesk-{version}-0.x86_64.rpm",
    )
    _try_rename(
        root / f"rustdesk-{version}-fedora28-centos8.rpm",
        root / f"wtdesk-{version}-fedora28-centos8.rpm",
    )

    # openSUSE RPM
    _try_rename(
        root / f"rustdesk-{version}-suse.rpm",
        root / f"wtdesk-{version}-suse.rpm",
    )

    # macOS dmg
    _try_rename(
        root / f"rustdesk-{version}.dmg",
        root / f"wtdesk-{version}.dmg",
    )

    # Windows 安装包
    if "windows" in system:
        # Flutter Windows 安装包：rustdesk-<ver>-install.exe
        _try_rename(
            root / f"rustdesk-{version}-install.exe",
            root / f"wtdesk-{version}-install.exe",
        )
        # 纯 Windows（非 Flutter）win7 安装包：rustdesk-<ver>-win7-install.exe
        _try_rename(
            root / f"rustdesk-{version}-win7-install.exe",
            root / f"wtdesk-{version}-win7-install.exe",
        )

        # 可选：把 target/release/RustDesk.exe 也同步改名为 wtdesk.exe
        target_release = root / "target" / "release"
        _try_rename(
            target_release / "RustDesk.exe",
            target_release / "wtdesk.exe",
        )


def main():
    # 确保能导入同目录下的 build.py
    sys.path.insert(0, os.path.abspath(os.curdir))

    try:
        build = importlib.import_module("build")
    except ModuleNotFoundError:
        sys.stderr.write(
            "[wtdesk] 无法导入 build.py，请确认 build2.py 与 build.py 在同一目录下。\n"
        )
        sys.exit(1)

    # 先执行原始构建逻辑（与直接运行 build.py 一致）
    # 注意：build.main() 内部使用 argparse 解析 sys.argv，
    # 这里直接复用当前命令行参数即可。
    if not hasattr(build, "main"):
        sys.stderr.write("[wtdesk] 原始 build.py 中未找到 main() 函数。\n")
        sys.exit(1)

    build.main()

    # 构建完成后，读取版本号并重命名最终产物
    if not hasattr(build, "get_version"):
        sys.stderr.write("[wtdesk] 原始 build.py 中未找到 get_version() 函数。\n")
        sys.exit(1)

    version = build.get_version()
    if not version:
        print("[wtdesk] 未能从 Cargo.toml 读取版本号，跳过重命名。")
        return

    print(f"[wtdesk] detected version: {version}")
    _rename_outputs_to_wtdesk(version)


if __name__ == "__main__":
    main()


