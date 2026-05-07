# 快速开始指南

## 5分钟上手TradeClaw

### 第一步：安装依赖

```bash
# 创建虚拟环境（推荐）
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置API密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，添加您的DeepSeek API密钥
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**获取DeepSeek API密钥**：
1. 访问：https://platform.deepseek.com/
2. 注册并登录
3. 创建API Key
4. 复制API Key到 `.env` 文件

### 第三步：配置您的持仓

编辑 `config/holdings.yaml`：

```yaml
# 当前持仓
current_holdings:
  - code: "600519"  # 贵州茅台
    name: "贵州茅台"
    quantity: 100
    cost: 1650.00

# 历史交易（可选）
closed_trades:
  - code: "600519"
    name: "贵州茅台"
    buy_date: "2026-04-01"
    buy_price: 1600.00
    sell_date: "2026-04-15"
    sell_price: 1750.00
    quantity: 100
```

**股票代码格式**：
- 上海市场：600xxx, 601xxx, 603xxx, 605xxx
- 深圳市场：000xxx, 002xxx, 003xxx, 300xxx
- ETF：5xxxxx, 159xxx 等

### 第四步：运行系统

```bash
bash run_report.sh
```

等待3-5分钟，报告将生成在 `reports/` 目录。

---

## 🔧 高级配置

### 使用OpenAI替代DeepSeek

编辑 `.env` 文件：

```bash
DEEPSEEK_API_KEY=  # 留空或删除
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

然后在 `src/tradeclaw/crew.py` 中的LLM配置部分已包含OpenAI配置，系统会自动使用。

### 自定义LLM

编辑 `src/tradeclaw/crew.py`：

```python
llm = LLM(
    model="your-model-name",
    api_key="your-api-key",
    base_url="your-api-endpoint"
)
```

---

## 📊 查看生成的报告

报告位置：`reports/daily_report_YYYY-MM-DD.md`

### 在终端查看

```bash
cat reports/daily_report_*.md | less
```

### 转换为PDF

```bash
# 系统会自动尝试转换为PDF
# PDF文件与MD文件在同一目录
```

---

## 🐛 常见问题

### 1. API密钥错误

**问题**：提示API密钥无效

**解决**：
- 检查 `.env` 文件是否正确配置
- 确认API密钥没有多余空格
- 验证API密钥是否有效

### 2. 网络连接失败

**问题**：数据获取失败

**解决**：
- 检查网络连接
- 系统会自动尝试多个数据源
- 如果全部失败，请稍后重试

### 3. 报告生成缓慢

**问题**：生成时间超过5分钟

**解决**：
- 首次运行会较慢（需要下载模型）
- 后续运行会使用缓存，速度大幅提升
- 耐心等待，系统正在分析中

### 4. 持仓数据不显示

**问题**：报告中没有持仓分析

**解决**：
- 检查 `config/holdings.yaml` 格式是否正确
- 确认YAML缩进正确（使用空格，不要使用Tab）
- 查看控制台是否有错误信息

---

## 💡 使用技巧

### 1. 定期清理缓存

```bash
# 清除K线缓存（强制重新获取数据）
rm -rf memory/kline_cache/*.json

# 清除分析历史
rm -rf memory/analysis_history/*.json
```

### 2. 查看调试信息

```bash
# 查看详细运行日志
python -u -m tradeclaw.main
```

### 3. 自定义报告时间

编辑 `run_report.sh`：

```bash
today=$(date -d "2026-05-08" '+%Y-%m-%d')  # 指定日期
```

---

## 📞 获取帮助

- 查看文档：`docs/` 目录
- 提交Issue：[GitHub Issues]
- 联系方式：见README.md

---

**祝您使用愉快！投资顺利！** 📈
