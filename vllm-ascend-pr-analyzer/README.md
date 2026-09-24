# vllm-ascend-pr-analyzer

分析 vLLM Ascend 项目的 GitHub PR/MR 代码变更，生成结构化代码分析报告和开发范式总结，指导 vLLM Ascend 场景的后续开发。

## 触发词

对话中出现以下关键词/短语时，opencode 会自动加载本 skill：

| 类别 | 触发词 |
|------|--------|
| 核心触发 | `分析 vLLM Ascend 的 PR`、`分析 vllm-ascend/vllm_ascend 代码实现` |
| 范式类 | `总结 vLLM Ascend 开发范式`、`总结开发范式`（限 vLLM Ascend 语境） |
| 适配类 | `vLLM NPU 适配分析`、`vLLM Ascend 适配分析` |
| 组合示例 | `分析 vllm-project/vllm-ascend 的 PR 17492` |
| | `分析 PR 123 456，总结开发范式` |
| | `学习这个历史需求的代码实现方式（vLLM Ascend）` |

### 触发词设计说明（维护者参考）

- `description` frontmatter 中前置了具体关键词：`分析 vLLM Ascend 的 PR/MR`、`vllm-ascend/vllm_ascend`、`vLLM Ascend 开发范式`、`vLLM NPU 适配分析`
- 限定语境：仅在涉及 vLLM Ascend / NPU 适配时触发，不响应通用代码分析请求（那由 lingxi-miner 等处理）

## 使用示例

```
分析 vllm-project/vllm-ascend 的 PR 17492
分析 PR 123 200 300，输出目录 D:\result，总结该场景开发范式
```

## 结构

```
vllm-ascend-pr-analyzer/
├── README.md         ← 本文件（触发词与使用说明）
├── SKILL.md          ← 工作流定义（三阶段：采集→分析→范式总结）
├── scripts/          ← init_workspace.py / fetch_pr.py / fetch_diff.py
└── assets/           ← analyzer_template.md / summarizer_template.md
```
