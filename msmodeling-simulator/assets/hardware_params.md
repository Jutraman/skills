# msModeling 硬件参数建模参考

## 硬件参数表（Device 抽象，可自定义）

| 参数 | 说明 | 备注 |
|------|------|------|
| `mma_ops` | CUBE 算力 | 理论峰值 FLOPS |
| `gp_ops` | Vec 算力 | 理论峰值 OPS |
| `memory_size_bytes` | HBM 显存大小 | |
| `memory_bandwidth_bytes_ps` | HBM 显存带宽 | |
| `compute_efficiency` | 算力利用率 | **需实测校准更真实** |
| `memory_efficiency` | 访存利用率 | **需实测校准更真实** |
| `grid` | [node数, 卡数, Die数] | 三级拓扑 |
| `topologies:0` | node 间互联 | [带宽, latency等待, comm_efficiency] 单向 |
| `topologies:1` | node 内卡间互联 | 同上，单向 |
| `topologies:2` | 卡内 Die 间互联 | 同上，单向 |
| `static_cost` | (mma_op_cost_s, gp_op_cost_s[, comm_op_cost_s]) | 平台经验值：CUBE/Vec/通信算子等待时间 |

## 核心耗时公式

单算子总耗时：

```
static_cost + MAX( (Cube+Vec)计算时间, 通信时间, 搬入搬出访存时间 )
```

各项计算：

| 计算类型 | 公式 |
|----------|------|
| CPU 侧算子下发 | static_cost |
| 算子载入（XPU 侧等待） | static_cost |
| Cube 计算 | Cube算量 / Cube算力 × 算力利用率 |
| Vec 计算 | Vec算量 / Vec算力 × 算力利用率 |
| Scalar 计算 | 非瓶颈，可被掩盖 |
| 搬入数据 | 数据量 / 访存带宽 × 带宽利用率 |
| 搬出数据 | 同上 |
| 卡间通信 | 通信次数×通信时延 + 通信量/互联带宽×互联带宽利用率（多种通信算法取最小） |
| 服务化调度间隔 | serving_overhead_s 经验值 2ms |

注：计算量、访存量、通信量均按真实输入 shape 计算。

## Roofline 考虑因素清单

- Cube 计算耗时
- Vec 计算耗时
- 访存搬入/搬出数据量
- 数据卡间通信
- Device 算子调度耗时（static_cost 经验值）
- 服务化调度耗时（serving_overhead_s 经验值）

## 未建模因素（精度风险）

| 缺失项 | 影响 | 可行方案 |
|--------|------|----------|
| L1/L2 cache 缓存命中 | 访存偏乐观 | 补充硬件微架构信息 |
| 通算掩盖 | 通信与计算串行化，耗时偏高 | 编译自动识别多流掩盖 / 融合算子建模 |
| Swiglu、MLAPreprocess、DSA、LinearAttention 融合 | 相关算子按独立算子计 | 逐步适配接入 |
| MTP 与主模型权重共享 | MTP 显存偏高 | 待修复 |
| 非 DS 模型投机推理 | 类 MTP 建模，未精准匹配 Eagle3 等架构 | 待精准匹配 |
| shape 对效率的影响 | 利用率恒定假设 | 实测数据拟合 |
| CP/PP 并行 | 不支持 | 待支持 |
| 临时内存占用 | 显存评估偏小 | 待补充 |

## 自定义芯片规格（what-if 分析）

下一代芯片规划场景：复制现有硬件参数表，修改 `mma_ops`/`gp_ops`/带宽/拓扑等字段，即可快速对比不同规格组合的性能差异（如 Die 数、互联带宽对 TPOT 的影响）。
