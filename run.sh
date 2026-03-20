#!/bin/bash
# TradeClaw 运行脚本

# 关闭所有代理（可选）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
export no_proxy="localhost,127.0.0.1"

echo "🔄 运行 TradeClaw..."
echo "📍 当前目录: $(pwd)"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 激活虚拟环境..."
    source .venv/bin/activate
else
    echo "⚠️  未找到虚拟环境，请先运行: uv sync"
    exit 1
fi

# 运行
crewai run
