---
name: devflow
description: "从模糊需求推进到已审查实现的轻量开发工作流。用户要求 brainstorm、保存设计、并行多视角改进、实现和 review，或说‘走完整设计开发流程’时使用；全程应用 ponytail，在 options-monitor 中用 om-doc-hygiene 维护唯一设计真源，使用独立 subagents 并行挑战设计，以 planreview 作为实现前 gate，并用 deepreview 闭环实现问题。"
---

# Devflow

把一次开发任务按以下顺序推进：

```text
Brainstorm
-> Save Design
-> Parallel Design Panel
-> Improve Design
-> Planreview
-> Implementation
-> Deepreview
-> Closeout
```

这是一个轻量编排 skill。复用现有 skills，不复制它们的内部规则，也不替代项目 `AGENTS.md`。

## 全程规则

- 从第一步开始应用 `$ponytail`；如果它已经激活，继续使用，不重复初始化。
- 先读适用的 `AGENTS.md`、相关源码、测试、配置和现有文档，再提出设计。
- 源码、配置和测试事实优先于过时文档；发现冲突时修正文档，不让实现迎合错误文档。
- 同一事实只保留一个当前 owner。更新同一设计文档，不创建 `v2`、`final`、`revised` 等平行副本。
- 普通 finding 自动进入修复与复审循环；只有下方 stop condition 才暂停询问用户。
- 不自动 commit、push、merge、发布、部署或修改生产状态；这些边界需要用户分别授权。

## 1. Brainstorm

确认以下内容：

- goal、motivation、success signals；
- non-goals 和 scope boundary；
- 当前事实、约束和未知项；
- 候选方案及主要 trade-offs。

只有存在真实取舍时才列多个方案，通常不超过三个。推荐满足目标的最小方案，并说明为什么更复杂方案暂时不需要。
如果方案选择会改变产品行为、公共契约、数据模型或运维边界，先让用户确认；否则继续。

## 2. Save Design

在 `options-monitor` 仓库中应用 `$om-doc-hygiene`：

1. 读取 `docs/INDEX.md` 并找到当前 canonical owner；
2. owner 已存在时更新它；仅在没有合适 owner 时创建设计文档；
3. 保留事实、权限、状态、副作用、失败语义和生产安全边界；
4. 不把 `docs/plans/`、`docs/reviews/` 或 `docs/gateflow/` 误当成 living documentation。

其它仓库若没有 `om-doc-hygiene`，遵循该仓库的文档约定完成同样的 owner-first 写入，并明确说明未调用该 skill。

设计文档至少包含：

- goal / non-goals / success signals；
- current facts and constraints；
- chosen design and rejected alternatives；
- affected owners、contracts、data flow、state transitions 和 failure behavior；
- implementation slices；
- validation plan；
- risks and open questions。

记录最终 `design_doc` 路径，后续所有评审使用这一个文件。

## 3. Parallel Design Panel

设计首次落盘后，同时派发三个只读 subagents。三者读取同一个 `design_doc` 快照，不互相读取结论，也不得编辑文件：

1. **Architecture / ownership**：检查边界、耦合、真源、契约和现有模式复用。
2. **Failure / safety**：检查错误路径、状态机、并发、恢复、数据完整性、安全和运维风险。
3. **Simplicity / delivery**：检查过度设计、scope creep、slice 粒度、测试缺口和更小可行方案。

每个 subagent 只返回：

- 建议修改的文档位置；
- 可失败的具体场景；
- 直接证据或明确标记的假设；
- 建议改法、收益、代价和优先级；
- 未覆盖区域。

主 agent 对输出去重、核验证据并裁决为 `accepted`、`rejected-with-reason`、
`deferred-with-owner` 或 `needs-more-evidence`。不要把三份输出直接拼进设计文档。

如果当前环境没有 subagent 能力，按三个视角分别审查并明确披露独立性降低；不要假装执行了并行评审。

## 4. Improve Design

把 accepted 建议合并回同一个 `design_doc`。在 `options-monitor` 中再次应用 `$om-doc-hygiene`，确保改写后仍是
current-state 文档，而不是评审会话记录。

结构性改动发生后，可以再做一次只针对改动区域的并行复核。没有新证据时不要无限循环。

## 5. Planreview Gate

对最终 `design_doc` 调用 `$planreview`。

- `fail`：裁决 findings，更新同一个设计文档，然后重新运行 `$planreview`。
- `pass-with-risks`：仅当每个 residual risk 都有明确 owner、影响和后续去向时通过。
- `pass`：冻结设计，进入实现。

`planreview` 只负责 adversarial review；设计修改仍由主 agent 完成，并继续遵守 `$om-doc-hygiene`。
未经通过的设计不得进入 Implementation。

## 6. Implementation

按冻结设计的 slices 实现，每次只做当前 slice：

- 复用现有 owner、helper、标准库和已安装依赖；
- 修改最少文件，不为假设性 future work 抽象；
- 从真实入口追踪完整调用链，bug fix 落在共同 root owner；
- 运行能证明当前 slice 的最小测试，再运行项目要求的完整 validation；
- 实现事实改变设计时，先更新 `design_doc`；若涉及契约或架构变化，返回 Planreview Gate。

## 7. Deepreview Gate

实现和 validation 完成后，对正确 base 下的全部当前改动调用 `$deepreview`。

- 裁决每个 finding；accepted findings 做 root-cause fix 并运行相关验证。
- 重新调用 `$deepreview`，直到没有未修复的 accepted blocking finding。
- finding 若要求改变已冻结的架构、契约、schema 或产品行为，先回到 Improve Design 和 Planreview Gate。
- 实现导致 living docs 变化时，在 `options-monitor` 中用 `$om-doc-hygiene` 更新同一个 owner。

## 8. Closeout

最终只报告：

- `design_doc` 路径和 planreview 结论；
- 实现范围与 changed files；
- validation 命令和结果；
- deepreview artifact 与最终 finding 状态；
- residual risks、owner 和下一步；
- 未执行的 commit / push / merge / release / deploy 边界。

## Stop Conditions

仅在以下情况暂停：

- 需要用户在会显著改变行为或范围的方案间选择；
- 权威事实、文件 owner 或目标 base 无法确定；
- 需要 destructive、外部写入、生产操作或新的授权；
- validation 无法运行，且没有等价证据；
- finding 无法安全修复或 residual risk 无 owner。
