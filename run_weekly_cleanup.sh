#!/bin/bash

# run_weekly_cleanup.sh
# 请将此文件放在项目根目录，并确保具有可执行权限：chmod +x run_weekly_cleanup.sh

echo "[START] $(date) 每周知识合并清理开始..."

# 激活虚拟环境（如适用）
# source .venv/bin/activate

# 切换到项目路径（你可根据部署位置修改此路径）
cd "$(dirname "$0")"

# 执行 Python 合并与清理脚本
python3 scripts/weekly_cleanup.py

echo "[FINISH] $(date) 完成。日志已记录。"
