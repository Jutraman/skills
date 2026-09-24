---
name: vllm-ascend-pr-analyzer
description: 分析 vLLM Ascend 项目的 GitHub PR/MR 代码变更，生成结构化代码分析报告和开发范式总结，指导 vLLM Ascend 场景的后续开发。当用户提到分析 vLLM Ascend 的 PR/MR、分析 vllm-ascend/vllm_ascend 代码实现、总结 vLLM Ascend 开发范式、vLLM NPU 适配分析时使用此技能。
---

# vLLM Ascend PR 分析

分析 vLLM Ascend 项目的代码变更（GitHub PR 或本地代码片段），生成结构化的代码分析报告和开发范式总结。支持多个 PR 联合分析。

## 项目背景

vLLM Ascend（`vllm-project/vllm-ascend`）是 vLLM 在华为昇腾 NPU 上的硬件插件后端：
- 仓库结构：`vllm_ascend/` 为主代码目录，平台入口为 `platform.py`，核心模块包括 `worker/`、`model_executor/`、`attention/`、`quantization/`、`distributed/`、`sample/`、`ops/` 等
- 需求常见类型：NPU 算子适配/对齐、torchair 图模式支持、量化（W8A8、w4a16 等）、分布式并行、性能优化、版本跟进（vLLM/ torch_npu 升级适配）
- 代码上下文：上游 vLLM 主仓 + 本仓插件代码，很多改动是"继承上游类并覆写 NPU 行为"，分析时需注意上游基类与子类覆写关系

## 适用场景

- 用户需要分析一个或多个 vLLM Ascend 的 PR 代码实现
- 用户想学习某个历史需求（如某算子适配、某量化方案）的实现方式
- 用户想生成 vLLM Ascend 某场景的开发范式总结

## SKILL 目录结构

```
vllm-ascend-pr-analyzer/
├── SKILL.md          ← 本文件，工作流定义
├── scripts/
│   ├── init_workspace.py  ← 创建工作目录
│   ├── fetch_pr.py        ← GitHub PR 模式数据采集脚本（gh CLI）
│   └── fetch_diff.py      ← 代码片段模式数据采集脚本
└── assets/
    ├── analyzer_template.md    ← 代码分析报告模板（阶段二使用）
    └── summarizer_template.md  ← 范式总结默认模板（阶段三使用，可被用户自定义模板覆盖）
```

## 执行前检查

本技能支持两种工作模式：
- **PR模式**：从 GitHub（vllm-project/vllm-ascend 或用户指定仓库）拉取 PR 数据分析
- **代码片段模式**：从本地代码片段文件（.diff、.patch、.txt等）提取代码变更分析

在开始阶段一之前，确认以下内容：

**共性检查项**：
- 范式描述：本次分析目标场景的一句话描述（两种模式必填）
- 输出目录：结果保存目录（可选，默认当前目录）
- 范式模板：自定义范式总结模板路径（可选）

**PR模式专属**：
- 仓库：默认 `vllm-project/vllm-ascend`，可指定其他 GitHub 仓库（必填，有默认值）
- PR编号：一个或多个，用空格或逗号分隔（必填）
- 网络要求：需能访问 `api.github.com`（gh CLI 优先，其次匿名 API）。如环境需代理，请先设置 `HTTPS_PROXY`/`HTTP_PROXY` 环境变量再执行脚本；如仍无法访问，引导用户改用代码片段模式

**代码片段模式专属**：
- 代码变更：本地文件路径（必填）
- 仓库路径：用于补充代码上下文（可选）

**多仓库场景**：
- PR模式：如 `vllm-project/vllm-ascend 的 PR 100 200 和 vllm-project/vllm 的 PR 300`，需明确仓库与 PR 编号的对应关系
- 代码片段模式：如 `repoA 的 diff1.diff 和 repoB 的 diff2.diff`，需明确仓库与本地文件对应关系

当用户输入不符合要求时，停止执行并向用户确认。缺少范式描述时必须向用户询问，不可自行编造。

## 工作流程

本工作流程仅理解已有代码仓（只读），禁止对代码仓中的已有文件进行修改！

### 阶段一：数据采集

**输入**：用户提供的 PR 编号或本地代码片段文件路径
**输出**：`<WORKSPACE>/input/` 目录下的归档文件 + spec_desc.txt

**注意**：此阶段只归档文件，不读取用户提供的原始文件内容进行分析。

1. **创建 WORKSPACE**：执行 `scripts/init_workspace.py` 创建工作目录
   ```bash
   python scripts/init_workspace.py --output <输出目录>
   ```
   - 返回 `<WORKSPACE>` 路径（格式：`miner_{timestamp}_{run_id}`）
   - 后续所有步骤均使用此路径作为输出根目录

2. **采集数据**：根据工作模式执行相应脚本
   - **PR模式**：执行 `scripts/fetch_pr.py` 拉取 PR 数据（依赖 gh CLI 已登录或环境变量 token）
   - **代码片段模式**：执行 `scripts/fetch_diff.py` 归档用户提供的代码片段文件，不要先读取其内容
   - **多仓库场景**：对每个仓库分别调用脚本，传入相同的 `--workspace` 参数

   ```bash
   # PR模式
   python scripts/fetch_pr.py --repo <owner/repo> --ids <pr_id1> <pr_id2> ... --workspace <WORKSPACE>

   # 代码片段模式（每个文件单独调用）
   python scripts/fetch_diff.py --file <impl_file> --repo <仓库路径> --workspace <WORKSPACE>
   ```

3. **创建范式描述文件**：在 `<WORKSPACE>/input/` 下创建 `spec_desc.txt`，写入用户提供的范式描述

阶段一完成后目录结构：

```
<WORKSPACE>/input/
├── spec_desc.txt           ← 范式描述（由你创建）
├── {repo}_{pr_id}.md       ← PR模式：每个 PR 的标题/描述和代码 diff
├── diff_*.md               ← 代码片段模式：仓库路径信息+代码片段
└── ...
```

---

### 阶段二：代码分析

**输入**：`<WORKSPACE>/input/` 目录下的归档文件（来自阶段一）
**输出**：`<WORKSPACE>/analyzer.md`

**注意**：此阶段读取阶段一归档的文件内容进行分析。

1. **读取原始数据**：读取 `<WORKSPACE>/input/` 下的所有 `*.md` 代码变更文件
2. **综合分析**：读取 `assets/analyzer_template.md` 模板，按模板各章节要求分析需求描述和实现代码
3. **搜索仓库上下文**（可选）：如有本地代码仓路径或已配置 vLLM Ascend 源码，可进一步探索：
   - 注意"上游 vLLM 基类 vs 本仓 NPU 覆写"关系：很多类继承自 `vllm/` 中的基类（如 `AttentionBackend`、`WorkerBase`、`LinearBase` 等），分析时需说明覆写了哪些方法、为何覆写
   - 关注 `platform.py` 中的平台注册与特性开关（`use_v1`、`supported_features` 等）
   - 搜索相关的方法、类、关键字和错误消息；定位相关文件并推理根本原因
   - 识别本仓特有的写法和风格（如 `_ascend_` 前缀、`torch_npu` 调用约定、CANN/HCCL 相关约束）
   - 仅摘取与需求实现相关的代码片段，忽略无关代码
4. **生成报告**：按模板生成统一代码分析报告，保存至 `<WORKSPACE>/analyzer.md`。报告使用**中文**输出，Markdown 格式。

#### 分析质量准则

- **关联分析**：多 PR 时分析关联和共性，提取共同逻辑而非罗列；排除无关代码
- **忠于事实**：分析基于原始数据（`*.md`）或代码仓，不推断不存在的实现
- **技术准确**：分析彻底且技术上准确，使用 vLLM/Ascend 社区熟悉的术语（如 torchair、torch_npu、CANN、HCCL、MC2、graph mode、eager mode）
- **具体有见地**：引用真实文件路径、类名/函数名、diff 行号；重点写设计理由、约束和决策背后的"为什么"（如为何绕过某上游实现、为何需特定 NPU 约束）
- **深入全面**：输出前自查是否覆盖模板各方面，是否理解完整上下文
- **可操作性**：见解对未来开发者和新手有用，可迁移到后续类似 NPU 适配需求

---

### 阶段三：范式总结

**输入**：
- **一般性场景描述**：`input/spec_desc.txt`
- **历史案例分析报告**：`analyzer.md`（阶段二产出）
- **历史案例代码**：`input/*.md`（阶段一采集）
- **范式总结模板**：用户自定义模板优先；未指定用 `assets/summarizer_template.md`

基于分析报告和代码实现，针对一般性场景描述，遵循范式总结模板要求，生成全面的实施步骤总结，将具体实例抽象为同场景开发范式模板，用于指导后续同场景的 vLLM Ascend 需求开发。

抽象化过程指导：
- 关注 vLLM Ascend 插件机制相关的框架逻辑，提取核心步骤，忽略具体业务参数
- 将具体代码示例转化为通用模式（文件路径、类名/函数名等用通配符或描述性表示）
- 提炼通用约束条件（如 NPU 算子对齐限制、版本兼容性、CANN 版本要求）和注意事项

**输出**：按范式总结模板要求，输出 Markdown 格式中文报告，保存到 `<WORKSPACE>/summary.md`

#### 范式总结质量准则

- **完整性**：覆盖模板各章节，无明显遗漏
- **可操作性**：步骤完整具体，可指导后续同场景 vLLM Ascend 需求开发
- **抽象程度**：参考代码已一般化，不含具体业务参数、硬编码值
- **准确性**：忠实于 `analyzer.md` 的分析，不自行推断未体现的信息

### 产出说明

任务完成后，告知用户以下内容已保存至 `<WORKSPACE>` 目录：
- `input/`：原始输入数据（PR 或代码片段文件 + 范式描述）
- `analyzer.md`：代码分析报告
- `summary.md`：开发范式总结
