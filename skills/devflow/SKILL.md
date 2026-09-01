---
name: devflow
description: "从模糊需求推进到已审查实现的人工确认式开发工作流。用户要求 brainstorm、保存设计、并行多视角改进、实现和 review，或说‘走完整研发流程’时使用；全程应用 ponytail，以 om-doc-hygiene、独立 subagents、planreview 和 deepreview 推进；Save Design 自动衔接 Parallel Design Panel，Improve Design 自动衔接 Planreview，最终 Implementation 自动衔接 Deepreview，其余节点之间必须等待用户明确确认。"
---

# Devflow

把一次开发任务按以下顺序推进：

```text
Brainstorm
-> [Human Confirm]
-> Save Design
-> Parallel Design Panel
-> [Human Confirm]
-> Improve Design
-> Planreview
-> [Human Confirm]
-> Implementation
-> Deepreview
-> [Human Confirm]
-> Closeout
-> [Human Confirm Completion]
```

这是一个轻量编排 skill。复用现有 skills，不复制它们的内部规则，也不替代项目 `AGENTS.md`。

## 全程规则

- 从第一步开始应用 `$ponytail`；如果它已经激活，继续使用，不重复初始化。
- 先读适用的 `AGENTS.md`、相关源码、测试、配置和现有文档，再提出设计。
- 源码、配置和测试事实优先于过时文档；发现冲突时修正文档，不让实现迎合错误文档。
- 同一事实只保留一个当前 owner。更新同一设计文档，不创建 `v2`、`final`、`revised` 等平行副本。
- Save Design 完成后自动启动 Parallel Design Panel；Improve Design 完成后自动启动 Planreview；最终 Implementation 和 validation 完成后自动启动 Deepreview。除此之外，每个节点只执行当前节点范围，完成后必须暂停并等待用户明确确认。
- 除上述三处自动衔接外，review finding、测试通过、artifact 已生成或用户此前要求“走完整流程”都不构成下一节点授权。
- 不自动 commit、push、merge、发布、部署或修改生产状态；这些边界需要用户分别授权。

## Human Confirmation Gate

除 `Save Design -> Parallel Design Panel`、`Improve Design -> Planreview` 和 `Implementation -> Deepreview` 外，每个节点结束时：

1. 报告当前节点、产物路径、关键决策或 findings、实际验证和未决风险；
2. 说明下一节点及其将执行的动作；
3. 将状态标记为 `awaiting_user_confirmation`；
4. 明确询问用户是否进入下一节点，然后停止。

只有用户在看到本节点结果后明确回复“继续”“确认”“进入下一环节”或同等含义，才可推进。用户要求修改时留在当前节点，
修改完成后重新经过确认 gate。等待期间不得预启动下一节点的 subagents、编辑下一节点文件、调用下一节点 skill 或把下一节点写成已开始。

上下文恢复时先确认最后一个已获用户批准的节点；证据不清时保持 `awaiting_user_confirmation`，不要猜测。

## 1. Brainstorm

确认以下内容：

- goal、motivation、success signals；
- non-goals 和 scope boundary；
- 当前事实、约束和未知项；
- 候选方案及主要 trade-offs。

只有存在真实取舍时才列多个方案，通常不超过三个。推荐满足目标的最小方案，并说明为什么更复杂方案暂时不需要。
输出推荐方案和取舍后进入 `awaiting_user_confirmation`。用户确认选定方案后，才进入 Save Design。

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

报告文档路径、owner、写入内容和检查结果后，直接启动 Parallel Design Panel，无需等待用户确认。

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

汇总建议、证据和拟议裁决后进入 `awaiting_user_confirmation`。用户确认 accepted 建议后，才进入 Improve Design；此节点不得直接改设计文档。

## 4. Improve Design

把 accepted 建议合并回同一个 `design_doc`。在 `options-monitor` 中再次应用 `$om-doc-hygiene`，确保改写后仍是
current-state 文档，而不是评审会话记录。

结构性改动发生后，可以再做一次只针对改动区域的并行复核。没有新证据时不要无限循环。

报告设计变更和剩余风险后，直接调用 `$planreview`，无需等待用户确认。

## 5. Planreview Gate

对最终 `design_doc` 调用 `$planreview`。

- `fail`：报告 findings 和拟议修复，等待用户确认后再回到 Improve Design；不得自动修改或 re-review。
- `pass-with-risks`：仅当每个 residual risk 都有明确 owner、影响和后续去向时通过。
- `pass`：设计可冻结，但仍须等待用户确认后才能进入实现。

`planreview` 只负责 adversarial review；设计修改仍由主 agent 完成，并继续遵守 `$om-doc-hygiene`。
未经通过的设计不得进入 Implementation。

请求 Implementation 授权前，先做只读的 Workspace Isolation Check：

1. 读取项目 worktree 约定、`git status --short --branch`、`git worktree list --porcelain` 和预期 base；
2. 已处于本任务专用 worktree 时直接复用，不创建嵌套 worktree；
3. 已有 base 和任务范围匹配的专用 worktree 时优先复用；
4. 当前 checkout 仅包含本任务改动且不与其他工作共享时继续使用；
5. 当前 checkout 位于共享或受保护分支、包含无关改动，或并行实现可能冲突时，拟定从已验证 base 创建隔离 worktree；
6. base、worktree owner 或未提交改动归属不清时保持 `awaiting_user_confirmation`，不得猜测。

此检查只产生 `implementation_workspace`、`review_base` 和拟议动作，不创建 worktree、不切分支、不 stash、不移动文件。
报告 planreview artifact、结论、residual risks 和 workspace 决策后进入 `awaiting_user_confirmation`。用户明确批准实现后，才进入 Implementation。

## 6. Implementation

进入 Implementation 后先执行已批准的 workspace 决策，不再增加确认门：

- 复用当前或现有专用 worktree；只有只读检查判定需要隔离时才新建；
- 不自动 stash、reset、移动或清理无关改动；若需迁移，只迁移已核验的本任务文件，并确保目标 worktree 可读取同一个 `design_doc`；
- 实际 base 漂移、目标 worktree 被占用或批准条件不再成立时立即暂停；
- Implementation、validation 和 Deepreview 使用同一 `implementation_workspace` 和 `review_base`。

按冻结设计的 slices 实现，每次只做当前 slice：

- 复用现有 owner、helper、标准库和已安装依赖；
- 修改最少文件，不为假设性 future work 抽象；
- 从真实入口追踪完整调用链，bug fix 落在共同 root owner；
- 运行能证明当前 slice 的最小测试，再运行项目要求的完整 validation；
- 实现事实改变设计时，先更新 `design_doc`；若涉及契约或架构变化，返回 Planreview Gate。

每个非最终 slice 完成后报告 changed files、验证和偏差，并进入 `awaiting_user_confirmation`；用户确认后才能进入下一 slice。
最终 slice 和项目要求的 validation 完成后，报告 changed files、验证和偏差，然后直接调用 `$deepreview`，无需等待用户确认。

## 7. Deepreview Gate

实现和 validation 完成后，对正确 base 下的全部当前改动调用 `$deepreview`。

- 裁决每个 finding 并提出 root-cause fix；等待用户确认后才修复和 re-review。
- re-review 通过后仍须等待用户确认，不能自动进入 Closeout。
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

报告完成后进入 `awaiting_user_confirmation`。只有用户明确回复“完成”或同等含义，才把 workflow 标记为 completed。

## Additional Stop Conditions

除 `Save Design -> Parallel Design Panel`、`Improve Design -> Planreview` 和 `Implementation -> Deepreview` 三处自动衔接外，以下情况也必须暂停：

- 需要用户在会显著改变行为或范围的方案间选择；
- 权威事实、文件 owner 或目标 base 无法确定；
- 需要 destructive、外部写入、生产操作或新的授权；
- validation 无法运行，且没有等价证据；
- finding 无法安全修复或 residual risk 无 owner。
