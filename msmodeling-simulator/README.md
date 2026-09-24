# msmodeling-simulator

使用 msModeling（六壬）对 LLM/多模态模型在昇腾及友商硬件上做**纯仿真性能评估**与**部署参数寻优**，不依赖真实 Device。

## 触发词

对话中出现以下关键词/短语时，opencode 会自动加载本 skill：

| 类别 | 触发词 |
|------|--------|
| 工具名 | `msModeling`、`六壬`、`liuren_modeling`、`tensor_cast` |
| 仿真类 | `性能仿真`、`仿真评估`、`性能建模`、`无需真实硬件跑性能` |
| 评估类 | `性能评估`、`Roofline`、`Forward 耗时评估`、`TTFT/TPOT 评估` |
| 寻优类 | `部署参数寻优`、`最大并发`、`PD 配比`、`服务化性能` |
| 选型类 | `竞品性能对比`、`芯片选型分析`、`服务器选型` |
| 组合示例 | `用 msModeling 仿真 Qwen3-235B 在 16 卡 A2 上 W8A8 量化下的最大并发` |
| | `评估 DeepSeek-V3.1 decode 阶段 TPOT，H20 8卡，不量化` |
| | `对比 5 款 A5 服务器跑 Wan2.2 的性能` |

### 触发词设计说明（维护者参考）

- `description` frontmatter 前置关键词：`性能仿真`、`性能评估`、`性能建模`、`msModeling`、`六壬`、`Roofline`、`TTFT/TPOT`、`部署参数寻优`、`竞品性能对比`、`芯片选型`
- 限定语境：仅性能建模/仿真场景触发；真实上板性能测试、vLLM Ascend PR 分析不归本 skill 管

## 使用示例

```
用 msModeling 评估 Qwen2.5-7B decode：3000 上下文 16 并发 TP2，ATLAS_800_A2_376T_64G
Qwen3-235B-A22B 服务化寻优：输入3500 输出1500，TTFT<3s TPOT<0.05s，16卡，W8A8+compile
Wan2.2 720P 81帧 8卡 Ulysses4 CFG 并行的单次 forward 耗时
自定义下一代芯片规格：Die 数翻倍、互联带宽 ×1.5，对比 TPOT 变化
```

## 结构

```
msmodeling-simulator/
├── README.md                    ← 本文件（触发词与使用说明）
├── SKILL.md                     ← 工作流定义（环境确认→命令构造→执行解读→寻优迭代）
├── scripts/
│   └── check_env.py             ← msModeling 环境检查
└── assets/
    ├── scenario_commands.md     ← 三大场景命令手册
    ├── hardware_params.md       ← 硬件参数建模参考 + 耗时公式 + 精度风险
    └── report_template.md       ← 仿真评估报告模板
```
