# AI 投研多路融合分析助手

基于 **Dify 工作流** + **RAG 知识库** 的多路融合投研系统，通过意图分类将查询路由到基本面、市场情绪、量化技术面三条分支，分别调用知识库检索、实时搜索和量化数据计算，最终由 LLM 统一输出结构化分析报告。

## 系统架构

```
用户输入 (query + stock_symbol, e.g. 00700.HK)
       ↓
  问题分类器 (deepseek-v4-pro)
       ↓
   ┌──────────┼───────────┐
   ↓          ↓           ↓
 基本面      市场情绪     量化技术面
   ↓          ↓           ↓
 知识库检索   Serper搜索   Tushare API
 (Dify KB +  (Google      (港股日线)
  Rerank)    实时搜索)     ↓
   ↓          ↓           Code执行(MA5)
   ↓          ↓           ↓
 LLM 分析    LLM 情绪    LLM 量化
   ↓          ↓           ↓
 结构化报告  偏多/偏空/中性 技术面报告
```

## 项目组成

### 1. Dify 工作流 DSL (`dify/workflow_dsl.yml`)

可直接导入 Dify 的完整工作流定义，包含：
- **问题分类器**：3 路意图路由（fundamental / sentiment / quant）
- **知识库检索**：混合检索 + bge-reranker-v2-m3 重排
- **Serper 搜索**：Google 实时搜索获取市场舆情
- **Tushare HTTP + Code 执行**：获取港股日线数据，计算 MA5
- **3 个 LLM 节点**：各分支独立生成专业分析报告

### 2. PDF 预处理脚本 (`preprocessing/`)

对原始财报 PDF 进行噪音清理和核心章节提取，是 RAG 检索效果的关键前置步骤：

| 脚本 | 功能 |
|------|------|
| `analyze_pdf.py` | 分析 PDF 结构：页数、目录、章节标记 |
| `extract_sections.py` | 提取 7 个核心章节，清理 70-86% 噪音页 |
| `split_pdf.py` | 拆分大 PDF 为 <10MB 的片段，遵守章节边界 |
| `quant_compute.py` | 量化计算的独立 Python 版本（对应 Dify Code 节点）|
| `config.py` | 集中化配置：路径、章节定义、大小限制 |

**预处理效果（腾讯控股 2025 财报）：**

| 报告 | 原始 | 提取核心 | 噪音清理 |
|------|------|---------|---------|
| 年度报告 | 282 页 | 40 页 | 86% |
| 中期报告 | 122 页 | 37 页 | 70% |

### 3. 知识库配置指南 (`dify/knowledge_base_setup.md`)

详细说明 Dify 知识库的分段策略、检索模式、Rerank 配置和 Embedding 模型选择。

### 4. 测试用例 (`tests/test_cases.md`)

11 个分层测试用例，覆盖：
- 简单级：精确数字查询（总收入、净利润、MAU）
- 中等级：语义段落检索（增长驱动因素、分板块分析）
- 困难级：跨章节关联 + 因果推理
- 拒答测试：超出知识库范围的问题

## 快速开始

### 前置条件

- Dify 平台（自部署或云服务）
- deepseek-v4-pro API key（或替换为其他 LLM）
- Serper API key（Google 搜索）
- Tushare Pro token（港股数据）
- SiliconFlow API key（Rerank 模型）

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/SuMing-byte-an/AI-Research-Assistant.git

# 2. 安装预处理依赖（如需本地处理 PDF）
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API keys
```

**Dify 部署：**

1. 在 Dify 中创建新的 Workflow 应用
2. 导入 `dify/workflow_dsl.yml`
3. 安装依赖插件：deepseek、serper、siliconflow
4. 创建知识库，上传预处理后的财报文件
5. 在知识库检索节点中填入 Dataset ID
6. 在环境变量中填入 TUSHARE_TOKEN

**PDF 预处理（可选，如需自定义财报数据源）：**

```bash
# 分析 PDF 结构
python preprocessing/analyze_pdf.py raw_pdfs/Tencent_2025_Annual_Report.pdf

# 提取核心章节
python preprocessing/extract_sections.py --raw-dir raw_pdfs --out-dir processed

# 拆分大文件（如超过 Dify 上传限制）
python preprocessing/split_pdf.py --raw-dir processed --out-dir split
```

## 知识库关键配置

| 参数 | 推荐值 | 原因 |
|------|-------|------|
| 检索模式 | 混合检索 | 同时需要语义理解和关键词精确匹配 |
| Keyword Weight | 0.7 | 财报中精确数字和专有名词多 |
| Semantic Weight | 0.3 | 语义理解辅助 |
| Rerank | bge-reranker-v2-m3 | 重排后精准度显著提升 |
| 分段长度 | 1000 Tokens | 财务分析需要较长上下文 |
| Top K | 5 | 财报数据分散在多个段落 |

## 目录结构

```
AI-Research-Assistant/
├── README.md
├── LICENSE                    # MIT
├── .env.example
├── .gitignore
├── requirements.txt
├── dify/
│   ├── workflow_dsl.yml       # Dify DSL（可直接导入）
│   └── knowledge_base_setup.md
├── preprocessing/
│   ├── config.py              # 集中化配置
│   ├── analyze_pdf.py         # PDF 结构分析
│   ├── extract_sections.py    # 核心章节提取
│   ├── split_pdf.py           # 大文件拆分
│   └── quant_compute.py       # 量化计算（独立版本）
├── tests/
│   ├── test_cases.md          # RAG 命中测试用例
│   └── test_preprocessing.py  # 单元测试
└── docs/
│   ├── architecture.md        # 架构设计
│   └─ development.md          # 开发指南
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 工作流引擎 | Dify Workflow |
| LLM | deepseek-v4-pro (分类 + 3 路分析) |
| RAG 检索 | Dify Knowledge Base + bge-reranker-v2-m3 |
| 实时搜索 | Serper (Google Search API) |
| 量化数据 | Tushare Pro (港股日线 API) |
| Embedding | bge-large-zh-v1.5 / bge-m3 |
| PDF 处理 | PyMuPDF (fitz) + pdfplumber |

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
