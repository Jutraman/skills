# skills
OpenSkills for All Platforms。

## 分支约定

- **`dev`**：日常开发分支，所有新增/修改先在 dev 提交
- **`main`**：稳定分支，dev 验证通过后合回（PR 或本地 merge + push）

## 触发词说明

每个 skill 的 `README.md` 记录其**触发词**——用户对话中出现这些关键词时，opencode 会自动加载对应 skill 的 SKILL.md。新增 skill 时请同步维护其 README 的触发词章节。

## Skills 列表

| Skill | 说明 |
|-------|------|
| [vllm-ascend-pr-analyzer](./vllm-ascend-pr-analyzer/README.md) | 分析 vLLM Ascend 的 PR 代码变更，生成分析报告与开发范式总结 |
| [msmodeling-simulator](./msmodeling-simulator/README.md) | 使用 msModeling（六壬）做模型性能仿真评估与部署参数寻优，无需真实硬件 |
| [compute-card-specs](./compute-card-specs/README.md) | 采集国内外已发布算力卡规格并整合成对比表格，可溯源可校准 |

