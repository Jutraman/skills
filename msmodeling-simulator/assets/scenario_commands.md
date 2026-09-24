# msModeling 三大场景命令手册

> 仓库：`https://gitcode.com/Ascend/msmodeling`（分支 `msserviceprofiler_dev`）
> 所有命令均为纯仿真，不依赖真实 Device

## 场景 1：Forward 耗时评估

### 1.1 文本生成（LLM）

**decode 阶段**（Qwen2.5-7B，上下文 3000，16 并发，2 卡，TP2，不量化）：

```bash
python -m tensor_cast.scripts.text_generate Qwen/Qwen2.5-7B \
  --num-queries 16 \
  --query-length 1 \
  --context-length 3000 \
  --device ATLAS_800_A2_376T_64G \
  --world-size 2 \
  --decode \
  --tp-size 2 \
  --compile \
  --quantize-linear-action DISABLED
```

**prefill 阶段**：去掉 `--decode` 即可。

### 1.2 视频生成（多模态）

**Wan2.2-T2V，720P，81 帧，8 卡，Ulysses SP4，CFG 并行**：

```bash
python -m tensor_cast.scripts.video_generate "Wan2.2-T2V-A14B-Diffusers" \
  --seq-len 128 \
  --batch-size 1 \
  --height 720 \
  --width 1280 \
  --world-size 8 \
  --ulysses-size 4 \
  --frame-num 81 \
  --sample-step 1 \
  --device ATLAS_800_A2_376T_64G \
  --quantize-linear-action DISABLED \
  --use-cfg \
  --cfg-parallel
```

### 输出解读

- forward 总耗时（如 10.618ms）
- 各算子耗时与调用次数（如 mm 算子 85 次，平均 79.087us，总计 6.722ms）
- 显存占用
- bound 分析（未定义算子按 memory-bound 计）
- Chrome Trace（`chrome://tracing/` 可视化）

## 场景 2：服务化 Benchmark 寻优

**Qwen3-235B-A22B，16 卡，W8A8 量化，TTFT<3s、TPOT<0.05s 约束下找最大并发**：

```bash
python -m tensor_cast.scripts.benchmark \
  --model-id Qwen/Qwen3-235B-A22B \
  --device ATLAS_800_A2_280T_64G \
  --num-devices 16 \
  --input-length 3500 \
  --output-length 1500 \
  --ttft-limits 3 \
  --tpot-limits 0.05 \
  --quantize-linear-action W8A8_DYNAMIC \
  --compile
```

### 输出解读

- 工具自动遍历不同 TP 数
- 每个 SLO 下符合指标的最大并发数
- 对应 TPS、TPS/Device、算子耗时 bound 占比

## 场景 3：服务化仿真（PD 分离/混部）

```bash
python main.py \
  --instance_config_path=./example/instances.yaml \
  --common_config_path=./example/common.yaml
```

### 配置文件

**instances.yaml**：仿真硬件、PD 配比、并行策略
- PD 混部示例：prefill 与 decode 实例共享硬件，配比参数控制
- PD 分离示例：prefill/decode 实例独立硬件与并行

**common.yaml**：模型、benchmark、服务化推理框架参数

### 输出解读

- TTFT、TPOT、端到端时间、TPS
- 不同 PD 配比下的性能曲线

## 通用参数速查

| 参数 | 说明 | 默认/建议 |
|------|------|----------|
| `--model-id` / 位置参数 | HF 模型名或本地路径 | 必填 |
| `--device` | 设备型号（如 ATLAS_800_A2_376T_64G） | 必填 |
| `--num-devices` / `--world-size` | 总卡数 | 必填 |
| `--tp-size` | 张量并行 | 1 |
| `--ep-size` | MoE Expert 并行 | =EP |
| `--ulysses-size` | 序列并行（视频） | 1 |
| `--use-cfg` + `--cfg-parallel` | CFG 并行（视频） | 关 |
| `--compile` | 整图编译+算子融合 | 建议开（评估时间变长） |
| `--quantize-linear-action` | W8A8_DYNAMIC / DISABLED 等 | DISABLED |
| `--quantize-attention-action` | Attention 量化（int8） | DISABLED |
| `--mxfp4-group-size` | MXFP4 量化粒度 | — |
| `--num-mtp-tokens` | MTP 投机 token 数 | 0 |
| `--ttft-limits` / `--tpot-limits` | SLO，单位秒 | 仅 benchmark 需要 |
| `--reserved-memory-size-gb` | workspace 显存（OS/算子） | 按平台经验值 |
| `--decode` | decode 阶段开关 | 默认 prefill |

## 支持的硬件型号

A2/A3/A5、H20/H800/H100/H200/B30A、RTX4090/RTX6000D、P800、PPU、MLU590/MLU690

互联：UB/RoCE/NVLink/Infiniband/PCIE
