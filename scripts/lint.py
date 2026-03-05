#!/usr/bin/env python3
"""
Pylint 代码检查工具
"""

import subprocess
import sys


def run_pylint(files=None, fail_under=8.0):
    """运行 pylint 检查"""
    cmd = [
        "pylint",
        "--rcfile=.pylintrc",
        f"--fail-under={fail_under}",
    ]

    if files:
        cmd.extend(files)
    else:
        # 检查 src 目录下所有 Python 文件
        cmd.append("src/")

    result = subprocess.run(cmd, capture_output=False, check=False)
    return result.returncode


def main():
    """检查变更的文件"""
    # 获取变更的 Python 文件
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=False
    )

    files = [
        f.strip() for f in result.stdout.split("\n")
        if f.strip().endswith(".py")
    ]

    if not files:
        print("✅ 没有 Python 文件需要检查")
        return 0

    print(f"🔍 检查 {len(files)} 个 Python 文件...")
    return run_pylint(files)


def lint_all():
    """检查所有文件"""
    print("🔍 检查所有 Python 文件...")
    return run_pylint()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        sys.exit(lint_all())
    else:
        sys.exit(main())
