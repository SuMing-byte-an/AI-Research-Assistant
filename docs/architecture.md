# 架构设计

## 系统概述

AI 投研多路融合分析助手是一个基于 **Dify 工作流** 的金融研究系统，核心设计思路是将用户查询通过意图分类器路由到三条并行分支，分别处理基本面、市场情绪和量化技术面三类问题。

## 工作流架构

```
用户输入 (query + stock_symbol)
       ↓
  问题分类器 (deepseek-v4-pro, temperature=0.1)
       ↓
   ┌──────────┼───────────┐
   ↓          ↓           ↓
 基本面      市场情绪     量化技术面
 (fundamental) (sentiment)  (quant)
   ↓          ↓           ↓
 知识库检索   Serper搜索   Tushare HTTP
 (Dify KB +  (Google      (港股日线数据)
  Rerank)    实时搜索)
   ↓          ↓           ↓
 LLM 基本面   LLM 情绪    Code计算→LLM量化
 分析报告     判定报告     分析报告
   ↓          ↓           ↓
 输出1       输出3        输出2
```

## 核心节点说明

### 问题分类器
- 模型：deepseek-v4-pro
- Temperature：0.1（低随机性，确保分类稳定）
- 三个分类：
  - `fundamental`：基本面 / 财报数据 / 营收利润
  - `sentiment`：市场情绪 / 新闻舆情 / 宏观事件
  - `quant`：技术面 / K线 / 均线 / 量化因子

### 知识库检索节点（基本面分支）
- 检索模式：混合检索 (Hybrid Search)
- Keyword Weight：0.7 / Semantic Weight：0.3
- Rerank：bge-reranker-v2-m3
- Top K：5，Score Threshold：0.1

### Serper 搜索节点（情绪分支）
- 使用 Dify 内置的 Serper 插件
- 搜索关键词来自用户输入的 `stock_symbol`

### Tushare HTTP + Code 执行（量化分支）
- HTTP 请求：调用 Tushare Pro API 获取港股日线数据
- Code 执行：JavaScript 代码解析返回数据，计算 5 日均线 (MA5)，生成技术面特征描述
- Tushare Token 通过 Dify 环境变量注入（不在 DSL 中硬编码）

### LLM 节点（3 个）
- 模型：deepseek-v4-pro
- Temperature：0.7（允许一定创造性，但保持专业性）
- 每个 LLM 节点都有明确的 System Prompt，要求基于上下文回答、标注数据来源、使用 Markdown 表格

## PDF 预处理流程

这是 RAG 效果的关键前置步骤，独立于 Dify 工作流：

```
原始 PDF (282页年报 / 122页中报)
       ↓
  analyze_pdf.py → 识别章节结构
       ↓
  extract_sections.py → 提取7个核心章节
       ↓
  清理86%噪音页 → 核心章节合集 (40页 / 37页)
       ↓
  split_pdf.py → 按章节边界拆分 (<10MB)
       ↓
  上传到 Dify 知识库
```

### 噪音清理策略

从财报中删除的低价值页面：
- 封面 / 目录 / 释义页
- 董事会报告 / 企业管治（含高管照片和致辞）
- 独立核数师（审计师）报告
- 合同 / 法律声明 / 免责声明

保留的核心页面：
- 务概要（一页速览全貌）
- 主席报告（管理层定调）
- MD&A（分板块详细分析 — 最核心）
- 四大财务报表（精确数字）
