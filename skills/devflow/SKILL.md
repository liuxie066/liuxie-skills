---
name: devflow
description: "从模糊需求推进到已审查实现的人工确认式开发工作流。用户要求 brainstorm、保存设计、并行多视角改进、实现和 review，或说‘走完整研发流程’时使用；全程应用 ponytail，以 om-doc-hygiene、四个独立 reviewers（含可用时的 DSH Crew）、planreview 和 deepreview 推进；Save Design 自动衔接 Parallel Design Panel，Improve Design 自动衔接 Planreview，最终 Implementation 自动衔接 Deepreview，其余节点之间必须等待用户明确确认。"
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
- 用户确认 Brainstorm 后，确认的 goal、non-goals、scope 和 success signals 形成 binding scope contract。后续 design decision、slice 和 validation 必须映射到该 contract 或实现它所必需的 correctness/safety 条件；其它 finding 只能 `deferred-with-owner`，或在确需改变 contract 时暂停并请求用户重新确认，不得在 Improve Design、Planreview 或 Implementation 中自动扩大范围。
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

implementation slice 必须是可独立验证的行为增量，不按文件、模块或 owner 机械拆分；默认不超过 3 个，超过时先尝试合并，并在 `design_doc` 说明无法合并的原因。

记录最终 `design_doc` 路径，后续所有评审使用这一个文件。

报告文档路径、owner、写入内容和检查结果后，直接启动 Parallel Design Panel，无需等待用户确认。

## 3. Parallel Design Panel

设计首次落盘后，派发四个只读 reviewers。四者读取同一个 `design_doc` 快照，不互相读取结论，也不得编辑文件：

1. **Architecture / ownership**：检查边界、耦合、真源、契约和现有模式复用。
2. **Failure / safety**：检查错误路径、状态机、并发、恢复、数据完整性、安全和运维风险。
3. **Simplicity / delivery**：检查过度设计、scope creep、slice 粒度、测试缺口和更小可行方案。
4. **DSH Crew adversarial critic**：由主会话直接调用 DSH Crew worker，从跨视角寻找错误假设、反例、遗漏约束和前三个 reviewer 都可能忽略的风险。

第四个 reviewer 启动前先检查当前主会话是否提供全局 DSH Crew `dsh_spawn_worker` 或 `dsh_run_worker`。可用时必须由主会话直接调用，设置 `tier=pro`；可并行时优先 `dsh_spawn_worker`，分批执行时可用 `dsh_run_worker`，只读并行任务才可设置 `allow_concurrent_cwd=true`。使用 spawn 后必须通过 `dsh_worker_result` 取得最终结果，不得把 job id 或运行状态当成 review。不得先 spawn `ds-pro` / `ds-flash` Codex subagent 代为调用；当前 Codex 子代理不继承主会话的 DSH Crew MCP tools。

DSH brief 必须自包含：给出 `design_doc` 和仓库绝对路径、只读边界、验收标准、禁止修改/commit/push，并要求区分直接证据与假设。设计判断固定使用 `tier=pro`，不为节省成本降为 `tier=flash`。

容量允许时四者并行；并发槽不足时可分批，但后启动者仍只接收同一原始快照，不得看到先完成者的结论。DSH Crew 未安装、未向主会话暴露上述 tools、被禁用、dispatch 失败或结果读取失败时，用第四个原生 subagent 执行同一职责，不减少 reviewer 数量；不得为运行本节点自动安装、启动或配置 DSH Crew。

汇总时报告 `dsh_crew_status=used|fallback:<reason>`、`reviewer_backend`、`reviewer_model` 和 `independence`。`reviewer_model` 只记录实际结果中可验证的模型身份，否则写 `unknown`；只有证据表明 reviewer 与主 agent 属于不同模型家族时，`independence` 才能写 `verified`，否则写 `unverified`，原生 fallback 写 `native-fallback`。

每个 reviewer 只返回：

- 建议修改的文档位置；
- 可失败的具体场景；
- 直接证据或明确标记的假设；
- 建议改法、收益、代价和优先级；
- 未覆盖区域。

主 agent 对输出去重、核验证据并裁决为 `accepted`、`rejected-with-reason`、
`deferred-with-owner` 或 `needs-more-evidence`。不要把四份输出直接拼进设计文档。

如果当前环境没有 subagent 能力，按四个视角分别审查并明确披露独立性降低；不要假装执行了并行评审。

汇总建议、证据和拟议裁决后进入 `awaiting_user_confirmation`。用户确认 accepted 建议后，才进入 Improve Design；此节点不得直接改设计文档。

## 4. Improve Design

把 accepted 建议合并回同一个 `design_doc`。在 `options-monitor` 中再次应用 `$om-doc-hygiene`，确保改写后仍是
current-state 文档，而不是评审会话记录。

结构性改动发生后，可以再做一次只针对改动区域的并行复核。完成初次改进后直接进入 Planreview Gate；后续普通高、中 finding 由下述有界循环回写同一个 `design_doc`，不增加人工确认门。

## 5. Planreview Gate

对最终 `design_doc` 调用 `$planreview`。

要求 `planreview` 检查每个 design decision、slice 和 validation 的 goal alignment，以及 slice 是否按可验证行为切分、是否可以合并；不得把 contract 外的改进机会升级为当前实现要求。

执行最多五轮 design-review loop；一次完整 `$planreview` 算一轮，首次 review 是第 1 轮：

1. 对每个 finding 核验证据并裁决；无效 finding 以理由关闭。
2. 对已选方向内有效的高、中 finding 做最小设计修正，更新同一个 `design_doc`；在 `options-monitor` 中继续应用 `$om-doc-hygiene`。
3. 对完整 `design_doc` 再次调用 `$planreview`，不得只审刚改的章节。
4. 重复至没有未关闭的有效高、中 finding，或完成第 5 轮。

低风险 finding 不阻塞循环；`pass-with-risks` 仅在没有未关闭的有效高、中 finding，且每个 residual risk 都有明确 owner、影响和后续去向时成立。若第 5 轮后仍有有效高、中 finding，报告逐项状态、阻塞原因和每轮 artifact，进入 `awaiting_user_confirmation` 并明确询问用户如何处理；未经明确确认不得启动第 6 轮，也不得冻结设计或进入 Implementation。

finding 若要求重新选择 goal/non-goals、产品方向或行为、scope、public contract、schema、architecture/owner、安全/权限边界或不可逆副作用，停止自动改进并请求用户决策；需要新的外部或生产授权时同样暂停。循环不得替用户做策略选择或扩大授权。

`planreview` 只负责 adversarial review；设计修改仍由主 agent 完成，并继续遵守 `$om-doc-hygiene`。
未经上述退出条件通过的设计不得进入 Implementation。所有有效高、中 finding 关闭后冻结设计，再执行 Workspace Isolation Check；进入 Implementation 仍需用户明确批准。

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

### Implementation Scope Drift Guard

进入 Implementation 时，以冻结的 `design_doc`、`implementation_workspace` 和当前 Git 状态记录
`implementation_baseline`，不创建新的状态文件。

每个 slice 开始前明确对应的 approved success signal、本 slice 交付的行为、expected owners / files 和 validation 命令。
每项实际修改必须归类为：

- `planned`：冻结设计已经要求；
- `required-correctness/safety`：不修改就会使 approved behavior 错误或不安全，且能给出具体 failure path 和对应 success signal。

邻近 cleanup、风格调整、顺手重构、future-proofing、额外监控以及 reviewer 建议本身，都不构成
`required-correctness/safety`。

每个 slice 完成后，使用 Git diff 对照 `implementation_baseline` 检查实际 changed files 和新增行为。无法映射到上述两类的修改不得进入下一 slice：仅属于本 agent 的改动应移除；有价值的发现记录为 `deferred-with-owner`；归属不明或确需改变 scope contract 时暂停并请求用户确认。

Review finding 不是扩大实现范围的授权。只有阻塞 approved success signal 或证明当前实现存在 correctness/safety 缺陷的 finding 才能进入当前修复循环。

### Implementation Model Routing

模型路由不增加人工确认门；主 agent 始终负责设计一致性、集成、validation 和 Deepreview。

Implementation slice 同时满足以下条件时，若当前原生 subagent 支持目标模型，优先使用
`model=gpt-5.6-luna`、`reasoning_effort=max`：

- 冻结设计已经明确行为和实现方向，不需要 worker 做新的设计决策；
- scope、owner、验收标准和测试命令清晰；
- 改动局部、可独立验证，失败后可以安全回退；
- 不涉及 public contract、schema、architecture/owner、权限/安全、并发/状态机、migration、数据完整性或不可逆副作用。

委派 brief 必须包含 `design_doc`、workspace、review base、slice 范围、预期行为、文件 ownership 和 validation 命令，
说明 worker 不是唯一改动者、不得回退他人修改，并禁止扩大范围、commit、push、merge、release 或 deploy。

主 agent 必须核对实际 diff 和测试证据。Luna 结果未通过验收、需要跨越上述边界或出现新的策略性选择时，立即收回主 agent
处理，不让 worker 自主扩大范围。目标模型或 subagent 不可用时直接由主 agent 实现，不阻塞流程。所有改动仍进入相同的完整
validation 和 Deepreview；不得因为使用 Luna 降低验收标准。

按冻结设计的 slices 连续实现。slice 是执行和进度报告单位，不是确认门：

- 复用现有 owner、helper、标准库和已安装依赖；
- 修改最少文件，不为假设性 future work 抽象；
- 从真实入口追踪完整调用链，bug fix 落在共同 root owner；
- 运行能证明当前 slice 的最小测试，再运行项目要求的完整 validation；
- 普通实现取舍、可修复的编译或测试失败不暂停；诊断、修复并继续下一 slice；
- 实现事实与设计记录不一致但不改变策略时，更新同一个 `design_doc` 后继续；
- 只有实现需要改变 goal/non-goals、产品行为、public contract、schema、architecture/owner、安全或权限边界、不可逆副作用，或需要新的用户授权时，才暂停并返回相应设计/确认节点。

每个 slice 完成后简要报告 changed files、验证和偏差，随后直接继续下一 slice，不进入 `awaiting_user_confirmation`。全部 slices 和项目要求的 validation 完成后，报告汇总结果并直接调用 `$deepreview`，无需等待用户确认。

## 7. Deepreview Gate

实现和 validation 完成后，对正确 base 下的全部当前改动调用 `$deepreview`。

执行最多五轮 review-remediation loop；一次完整 `$deepreview` 算一轮，首次 review 是第 1 轮：

1. 对每个 finding 核验证据并裁决；无效 finding 以理由关闭。
2. 对有效的高、中 finding 做共同 root owner 上的最小修复，运行针对性测试和项目要求的 validation。
3. 使用同一个 `implementation_workspace` 和 `review_base` 对全部当前改动再次调用 `$deepreview`，不得只审刚修的文件。
4. 重复至没有未关闭的有效高、中 finding，或完成第 5 轮。

低风险 finding 不阻塞循环；只记录明确 owner、影响和后续去向，不为清零低风险项扩大范围。若第 5 轮后仍有有效高、中 finding，报告逐项状态、阻塞原因和已验证证据，进入 `awaiting_user_confirmation` 并明确询问用户如何处理；未经用户明确确认不得启动第 6 轮，也不得宣称通过。

finding 若要求改变已冻结的 goal、产品行为、架构、public contract、schema、安全/权限边界或不可逆副作用，停止自动修复，回到 Improve Design 和 Planreview Gate；需要 destructive、外部写入、生产操作或新授权时同样暂停。循环不得绕过这些边界。

实现或修复导致 living docs 变化时，在 `options-monitor` 中用 `$om-doc-hygiene` 更新同一个 owner。所有有效高、中 finding 关闭后，报告每轮 artifact、修复和 validation，再进入 `awaiting_user_confirmation`；未经确认不能进入 Closeout。

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
