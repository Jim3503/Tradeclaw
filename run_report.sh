#!/bin/bash
# 立即刷新输出的运行脚本

cd /home/ming/ai-projects/daily-report/tradeclaw

echo "=========================================="
echo "📊 A股市场每日早报生成系统"
echo "=========================================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 激活虚拟环境并运行
source .venv/bin/activate

# 设置PYTHONPATH
export PYTHONPATH=/home/ming/ai-projects/daily-report/tradeclaw/src:$PYTHONPATH

# 运行系统（禁用Python缓冲）
python -u -m tradeclaw.main 2>&1 | while IFS= read -r line; do
    echo "$(date '+%H:%M:%S') | $line"
done

echo ""
echo "=========================================="
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
