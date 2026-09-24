---
name: msmodeling-simulator
description: 使用 msModeling（六壬）对 LLM/多模态模型在昇腾及友商硬件上做性能仿真评估与部署参数寻优。当用户提到性能仿真、性能评估、性能建模、msModeling、六壬、Roofline、TTFT/TPOT 评估、部署参数寻优、竞品性能对比、芯片选型分析、无需真实硬件跑性能时使用此技能。
---

# msModeling 性能仿真

使用 msModeling（六壬，`tensor_cast` / `liuren_modeling`）对模型在指定硬件上进行**纯仿真性能评估**与**部署参数寻优**，不依赖真实 Device。

## 项目背景

msModeling 是昇腾统一性能建模工具（仓库：`https://gitcode.com/Ascend/msmodeling`，开发分支 `msserviceprofiler_dev`，目录 `liuren_modeling`）：

- **原理**：在简化虚拟硬件模型上估计 PyTorch 模型性能。单算子耗时 = `static_cost + MAX((Cube+Vec)计算时间, 通信时间, 搬入搬出访存时间)`
- **算子建模两条路径**：Roofline 理论建模（默认）；实测性能数据拟合（更准）
- **硬件支持**：A2/A3/A5、H20/H800/H100/H200/B30A、RTX4090/RTX6000D、P800、PPU、MLU590/MLU690
- **互联**：UB/RoCE/NVLink/Infiniband/PCIE
- **模型支持**：DeepSeek-V3.1、Qwen2.5/Qwen3、Kimi-K2、GLM-4.5/4.6、ERNIE-4.5、minimax_m2、Wan2.1/2.2、HunyuanVideo 等（Transformers/Diffusers 自动接入）
- **特性**：compile 图编译、MTP、并行切分（TP/DP/EP/Ulysses/CFG）、量化（linear: w8a8/w4a8/mxfp8/mxfp4；attn: int8）、PD 分离/混部、KVCache/通信建模
- **输出**：Forward 耗时拆解（各算子耗时/调用次数）、显存占用、bound 分析、Chrome Trace、服务化 TPS/TTFT/TPOT 曲线
- **已知局限**：精度约 0.8；未建缓存/通算掩盖；部分融合算子（Swiglu、MLAPreprocess、DSA）未建模；MTP 未考虑权重共享；服务化 overhead 经验值 2ms

## 适用场景

- 用户需要**不依赖真实硬件**快速评估某模型在某硬件上的性能（TTFT/TPOT/吞吐）
- 用户需要服务化部署参数寻优：给定 SLO（ttft-limits/tpot-limits）找最大并发/最优并行策略/PD 配比
- 用户需要竞品性能 PK、服务器选型（如 DeepSeek 在 5 款 A5 服务器上的对比）
- 用户需要分析 Forward 耗时拆解、算子瓶颈、显存占用
- 用户需要自定义芯片规格（下一代芯片规划）做 what-if 分析

## SKILL 目录结构

```
msmodeling-simulator/
├── SKILL.md                       ← 本文件，工作流定义
├── README.md                      ← 触发词与使用说明
├── scripts/
│   └── check_env.py               ← msModeling 环境检查
└── assets/
    ├── scenario_commands.md       ← 三大场景命令手册（评估/寻优/服务化仿真）
    ├── hardware_params.md         ← 硬件参数建模参考表
    └── report_template.md         ← 仿真评估报告模板
```

## 执行前检查

在开始前确认以下内容，缺项时向用户询问：

**必填项**：
- **模型**：HuggingFace 模型名（如 `Qwen/Qwen2.5-7B`）或本地 Diffusers 模型路径
- **硬件**：设备型号（如 `ATLAS_800_A2_376T_64G`）+ 卡数（num-devices）
- **场景类型**：三选一
  1. Forward 耗时评估（文本生成 / 视频生成）
  2. 服务化 benchmark 寻优（给定 SLO）
  3. 服务化仿真（PD 分离/混部，YAML 配置）

**场景 1 专属**：
- 文本：`--num-queries`（并发）、`--context-length`、`--query-length`、decode/prefill 阶段
- 视频：`--seq-len`、`--height/--width`、`--frame-num`、`--sample-step`、`--use-cfg`

**场景 2 专属**：
- `--input-length`、`--output-length`
- SLO：`--ttft-limits`（秒）、`--tpot-limits`（秒）
- 可选：量化（`--quantize-linear-action W8A8_DYNAMIC`）、`--compile`

**场景 3 专属**：
- `instances.yaml`（硬件、PD 配比、并行）与 `common.yaml`（模型、benchmark、服务化参数）路径

**通用可选项**：
- 并行：`--tp-size`、`--ep-size`、`--ulysses-size`、`--cfg-parallel`
- 量化：`--quantize-linear-action`（W8A8_DYNAMIC/DISABLED 等）、`--quantize-attention-action`、`--mxfp4-group-size`
- `--num-mtp-tokens`（MTP 投机）
- `--compile`（整图编译，精度更高但评估耗时从百毫秒升至分钟级）
- `--reserved-memory-size-gb`（workspace 显存）

**环境检查**：先执行 `scripts/check_env.py` 确认 msModeling 已安装可用。

## 工作流程

### 阶段一：环境确认

1. 执行 `python scripts/check_env.py --repo <msmodeling路径>`，确认：
   - msModeling 仓库存在且 `tensor_cast` 模块可导入
   - 模型可在本地/HuggingFace 获取（离线环境需提前下载）
   - 目标硬件型号在支持列表内（不在时引导用户用自定义硬件参数文件）
2. 环境不满足时给出明确的安装/配置指引，不猜测性继续执行

### 阶段二：构造仿真命令

1. 按 `assets/scenario_commands.md` 的命令模板，将用户需求映射为完整命令行
2. **参数校验清单**（逐项过）：
   - decode 评估必须带 `--decode`，否则默认 prefill
   - TP/EP 与卡数一致性：`num-devices = tp-size × dp-size`（MoE 的 EP 另算）
   - 量化与 compile 组合是否被支持（W8A8_DYNAMIC 通常需配 `--compile`）
   - 视频模型必填 `--frame-num --height --width --sample-step`
   - SLO 单位：ttft/tpot limits 均为秒
3. 把最终命令展示给用户确认后再执行

### 阶段三：执行与结果解读

1. 执行命令，捕获输出
2. 按 `assets/report_template.md` 生成仿真评估报告，重点解读：
   - **forward 总耗时**与 Top 算子拆解（调用次数 × 平均耗时）
   - **bound 分析**：compute-bound / memory-bound / communication-bound
   - 服务化场景：SLO 约束下的最大并发、TPS、TPS/Device、PD 配比
   - 显存占用是否超限（含 reserved_memory_size_gb）
3. 结合已知局限提示精度风险：评估值偏乐观时（如 Swiglu 等融合算子缺失），说明偏差来源
4. Chrome Trace 若生成，告知用户用 `chrome://tracing/` 打开查看 timeline

### 阶段四：寻优迭代（仅寻优/服务化仿真场景）

1. 遍历并行策略（TP 从小到大）、量化开关、MTP 开关，形成参数矩阵
2. 每轮记录：forward 耗时 / 最大并发 / TPS / 显存峰值
3. 输出最优参数组合与理论最佳性能，标注"基于 Roofline 理论值，实际部署需实测校准"
4. 多硬件对比场景：固定模型与场景，仅切换硬件型号，输出归一化性能比例表

## 质量准则

- **忠于工具输出**：报告中所有数字来自工具实际输出，禁止手工推算冒充仿真结果
- **标注理论属性**：明确区分 Roofline 理论值与实测校准值，提醒"评估结果在部分场景可能过于乐观"
- **参数可复现**：报告必须附完整命令行，让他人可一键复现
- **精度诚实**：引用精度约 0.8 的背景，列出未建模因素（缓存、通算掩盖、部分融合算子）对本次结论的影响方向

## 产出说明

任务完成后，告知用户以下内容已保存：
- 仿真命令（可复现）
- 仿真评估报告（按模板，Markdown）
- Chrome Trace 文件路径（如有）
- 寻优结论与最优参数表（如有）
