# 开发指南

## 环境准备

```bash
# 克隆仓库
git clone https://github.com/SuMing-byte-an/AI-Research-Assistant.git
cd AI-Research-Assistant

# 安装 Python 依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API keys
```

## PDF 预处理

### 1. 下载原始财报 PDF

从腾讯官方 IR 页面下载：
- https://www.tencent.com/zh-cn/investors/financial-reports.html
- 将 PDF 放入 `raw_pdfs/` 目录

### 2. 分析 PDF 结构

```bash
python preprocessing/analyze_pdf.py raw_pdfs/Tencent_2025_Annual_Report.pdf
```

这会输出：
- 嵌入式目录（TOC）
- 章节标记扫描结果
- 前 30 页逐页概览

### 3. 提取核心章节

```bash
python preprocessing/extract_sections.py --raw-dir raw_pdfs --out-dir processed
```

输出到 `processed/` 目录：
- 每个章节的独立 PDF + Markdown
- 合集 PDF + 合集 Markdown

### 4. 拆分大文件

Dify 对上传文件有大小限制（通常 15MB），如果合集 PDF 超限：

```bash
python preprocessing/split_pdf.py --raw-dir processed --out-dir split --max-size-mb 10
```

## Dify 工作流部署

### 1. 导入 DSL

- 在 Dify 中创建新的 Workflow 应用
- 点击右上角导入 → 上传 `dify/workflow_dsl.yml`
- 在知识库检索节点中替换 `<YOUR_DATASET_ID>` 为你创建的知识库 ID
- 在环境变量中填入 `TUSHARE_TOKEN`

### 2. 安装 Dify 插件

工作流依赖以下 Dify 插件：
- `langgenius/deepseek` — LLM 模型提供者
- `langgenius/serper` — Google 实时搜索
- `langgenius/siliconflow` — Rerank 模型 (bge-reranker-v2-m3)

在 Dify 插件市场安装后，工作流会自动识别。

### 3. 创建知识库

参见 `dify/knowledge_base_setup.md` 的详细配置指南。

### 4. 测试

参见 `tests/test_cases.md` 的分层测试用例。

## 量化数据独立测试

如果只想测试量化分支的数据获取和计算：

```bash
export TUSHARE_TOKEN=your_token_here
python preprocessing/quant_compute.py --symbol 00700.HK --days 5
```

这会输出最近 5 个交易日的收盘价、5 日均线和技术面判定。

## 项目目录结构

```
AI-Research-Assistant/
├── README.md                    # 项目说明
├── LICENSE                      # MIT License
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git 忽略规则
├── requirements.txt             # Python 依赖
├── dify/
│   ├── workflow_dsl.yml         # Dify 工作流 DSL（可直接导入）
│   └── knowledge_base_setup.md  # 知识库配置指南
├── preprocessing/
│   ├── __init__.py
│   ├── config.py                # 集中化配置（路径、章节定义）
│   ├── analyze_pdf.py           # PDF 结构分析
│   ├── extract_sections.py      # 核心章节提取
│   ├── split_pdf.py             # PDF 大文件拆分
│   └── quant_compute.py         # 量化计算（独立 Python 版本）
├── tests/
│   ├── test_cases.md            # RAG 命中测试用例
│   └── test_preprocessing.py    # 预处理单元测试
├── docs/
│   ├── architecture.md          # 架构设计文档
│   └── development.md           # 本文件
└── screenshots/                 # README 截图存放
```
