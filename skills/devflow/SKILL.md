---
disable-model-invocation: true
name: devflow
description: "从需求澄清推进到已验证、已审查实现的开发工作流。先根据代码事实建议简单或完整链路，由用户确认选择；两条链路都保留四人独立设计 Panel、实现验证和 Deepreview，完整链路另含 Planreview 和分阶段确认。不包含提交、发布或部署。"
---

# Devflow

Devflow 只解决研发问题，范围从需求澄清到已验证、已评审实现的 Closeout。先完成 Brainstorm，给出链路建议，由用户确认 scope 和所选链路后推进：

```text
简单 simple:
Save Design -> 四人 Parallel Design Panel
-> [确认建议、workspace 和后续实现]
-> Improve Design -> Implementation -> Deepreview -> Closeout

完整 full:
Save Design -> 四人 Parallel Design Panel
-> [确认建议] -> Improve Design -> Planreview
-> [确认 workspace 和实现] -> Implementation -> Deepreview -> Closeout
-> [Human Confirm Completion]
```

两条链路共用下文的节点和质量规则；简单链路减少单独的 Planreview 与确认次数，不减少 Panel 人数、独立性、验证或 Deepreview 覆盖。

这是一个轻量编排 skill。可用时复用现有 companion skills，缺失时使用下述受控 fallback；不复制它们的内部规则，也不替代项目 `AGENTS.md`。

## Path Selection

Brainstorm 根据真实入口、改动行为、影响范围、可逆性和验收证据给出 `simple` 或 `full` 建议：

- 推荐简单链路：需求和行为明确，改动局部且可独立验证，没有尚待决定的重大方案取舍。
- 推荐完整链路：有重大设计取舍，或改变跨系统契约、schema/migration、权限、并发/状态机语义、交易执行、资金/账本计算、幂等或数据恢复行为。文件多、代码长或仅位于这些模块中，不单独构成理由。

报告推荐链路、具体依据、两条链路的差别和未决问题，然后请用户明确选择简单或完整链路，并确认本次 scope；选择前只做本节点只读调查，不保存设计、不启动 Panel 或实现。没有答复不等于接受推荐；仅说“继续/确认”而不能确定选择时询问所选链路。用户已明确指定链路时保留其选择，只补充建议和差异，不重复索要同一个选择；scope 确认仍按 Brainstorm 执行。

建议不替用户决策。用户选与建议不同的链路时，按其明确选择执行；项目强制的检查、未决产品/安全问题及外部或生产授权不因选择简单链路而豁免。简单链路下项目强制要求 Planreview 时仍执行该 Gate，并在选择时说明；未执行的 Planreview 记为 `not-applicable`，不得写成 pass。

Panel 或实现中发现改变建议的新事实时，说明证据、受影响范围和建议，请用户确认是否切换链路；不自动升级或降级。需要改变 scope/策略时先暂停解决对应决定，路径选择本身不是范围变更授权。切换后复用仍有效的 scope、设计、四人 Panel 和验证证据，不重复跑已完成节点；新出现的或已失效的 Gate 必须完成，review 预算不重置。

## Capability Check

Brainstorm 前一次性检查 `$ponytail`、`$deepreview`，在 `options-monitor` 中再检查 `$om-doc-hygiene`；选定链路后仅在需要 Planreview 时检查 `$planreview`，否则记为 `not-applicable`；不得为运行 workflow 自动安装或配置它们。记录适用项的 `<skill>_status=used|fallback:unavailable`，不适用的 `$om-doc-hygiene` 记为 `not-applicable`：

- `$ponytail` 缺失时，直接执行本 skill 的最小范围、最小改动规则；
- `$planreview` 缺失时，由主 agent 对完整设计执行同等的 adversarial review，并产出本 Gate 要求的 artifact、findings 和 verdict；
- `$deepreview` 缺失时，由主 agent 对 `review_base` 下的完整当前改动执行 evidence-based review，覆盖真实入口、调用链、contracts 和 tests，并产出本 Gate 要求的 artifact、findings 和 verdict；
- `$om-doc-hygiene` 缺失时，包括在 `options-monitor` 中，都按目标仓库约定执行 owner-first 文档更新并披露 fallback。

## 全程规则

- `$ponytail` 可用时从第一步开始应用；如果已经激活，继续使用，不重复初始化。
- 先读适用的 `AGENTS.md`、相关源码、测试、配置和现有文档，再提出设计。
- 源码、配置和测试事实优先于过时文档；发现冲突时修正文档，不让实现迎合错误文档。
- 同一事实只保留一个当前 owner。更新同一设计文档，不创建 `v2`、`final`、`revised` 等平行副本。
- 用户确认 Brainstorm 后，确认的 goal、non-goals、scope 和 success signals 形成 binding scope contract。后续 design decision、slice 和 validation 必须映射到该 contract 或实现它所必需的 correctness/safety 条件；其它 finding 只能 `deferred-with-owner`，或在确需改变 contract 时暂停并请求用户重新确认，不得在 Improve Design、Planreview 或 Implementation 中自动扩大范围。
- 按所选链路图推进：Save Design 后自动启动四人 Panel，Implementation 和 validation 后自动启动 Deepreview，通过后自动 Closeout。完整链路 Improve Design 后自动 Planreview；简单链路在 Panel 后获得建议、workspace 和后续实现的合并授权，Improve Design 后直接实现（项目强制 Planreview 除外）。图中确认点必须暂停，其余节点连续执行。
- review finding、测试通过、artifact 已生成或仅选择链路都不构成实现授权；简单链路的合并授权只覆盖向用户明确展示过的后续工作。
- commit / push、创建或合并 PR、发布、部署、升级及生产操作不属于 Devflow 节点。用户另行要求时交给项目独立流程处理，不扩展本 workflow；Closeout 提供研发证据交接。

## Node Contract

每个节点开始前先确认输入，结束时只报告输出、退出条件和下一动作。节点不得用聊天历史替代输入，也不得把产物存在误判为节点通过。

| 节点 | 必要输入 | 必须输出 | 退出条件 |
| --- | --- | --- | --- |
| Brainstorm | 原始需求、当前事实、可用 PRD 交接 | 链路建议、用户选择、binding scope contract | 所选链路及 goal、non-goals、scope、success signals 已确认；否则留在本节点 |
| Save Design | 已确认的 scope contract、PRD 交接 | 唯一 `design_doc` | 设计覆盖目标、边界、行为、失败语义、切片和验证计划 |
| Parallel Design Panel | 同一 `design_doc` 快照 | 四个 reviewer 的可用结果和主 agent 裁决 | 四个 reviewer 均有可用结果；每条建议已裁决 |
| Improve Design | accepted findings、原 `design_doc` | 更新后的同一 `design_doc` | 未改变已批准 contract；完整链路进入 Planreview，简单链路满足实现前置条件后进入 Implementation |
| Planreview | 最终 `design_doc` | verdict、findings、workspace 决策 | 没有 blocking finding，或按规则停下等待用户处理 |
| Implementation | 已批准设计、workspace 决策、实现 baseline | 改动、验证结果、scope drift 结果 | 项目要求的 validation 完成；随后自动进入 Deepreview |
| Deepreview | 正确 review base 上的完整当前改动 | review artifact、verdict、finding 状态 | 没有 blocking finding；随后自动进入 Closeout |
| Closeout | 设计、实现、验证、review 证据 | closeout 摘要和未执行边界 | 简单链路报告后完成；完整链路等待用户确认完成 |

节点输出不足、无法解析、内容版本不一致或无法证明退出条件时，保持当前节点，不猜测通过。

## PRD -> Devflow Handoff

PRDflow 的保存或交接只是 Devflow 的输入，不等同于 Brainstorm、Save Design 或任何后续节点已通过。已保存的 PRD 在进入 Brainstorm 时提供一个最小交接块；不要复制完整聊天记录或整份 PRD：

```yaml
### Devflow Handoff
prd_doc: /absolute/path/to/prd.md
approval_record: "PRD 中批准记录的位置或引用"
goal: "已批准根目标"
non_goals: ["明确不做的事项"]
scope: ["本次范围"]
success_signals: ["可观察成功信号"]
current_facts: ["有来源的事实"]
open_questions: ["未决问题；阻塞产品决定单独标记"]
blockers: []
next_action: Brainstorm
```

Brainstorm 必须核对该交接块与原始需求；缺少 goal、边界或 success signals 时留在 Brainstorm 并补齐，不得在 Save Design 中替用户猜测。没有保存授权时，交接只保留在会话中，不虚构 `prd_doc` 路径。

## Review Completion Rule

下文 `blocking finding` 统一指有效且未关闭的 `严重`、`高`、`中` finding。所有 review 节点 fail closed：调用失败，结果缺失、无法解析或自相矛盾，或 scope / evidence 被截断到不足以支持结论时，标记为 `review-unusable`；不得视为“无 finding”、`pass`、`pass-with-risks` 或节点完成。

两条链路的 Parallel Design Panel 都只有在四个所需 reviewer 均返回可用结果时才算完成。适用的 Planreview 和所有 Deepreview 都只有在 artifact 与 verdict 可用且没有 blocking finding 时才能通过。

Planreview 和 Deepreview 共用以下重审规则，分别计数；Panel 使用其节点内的重试规则：

1. 每个 Gate 最多五次 review attempt，首次为第 1 轮，每次调用尝试（含失败）都占预算。`review-unusable` 只能在剩余预算内补足证据后重审，不得进入 finding remediation。
2. 先逐项核验可用结果并裁决，无效 finding 以理由关闭；由主 agent 合批修正本轮范围内全部有效 blocking findings，按对应 Gate 完成验证后再完整重审，不逐条 finding 触发完整复审。重复至通过或耗尽预算；策略性问题或新授权仍立即暂停，不等批次完成。
3. 低风险 finding 不阻塞，也不为清零而扩大范围；每个 residual risk 必须有 owner、影响和后续去向。`pass-with-risks` 仅在这些条件满足且没有 blocking finding 时成立。
4. 第 5 轮后仍有 blocking finding 或没有可用 verdict 时，报告逐项状态、阻塞原因、每轮 artifact 和已验证证据，进入 `awaiting_user_confirmation` 并询问用户如何处理；未经明确确认不得启动第 6 轮，也不得宣称通过或进入下一节点。

### Review Dispatch Check

调用前在当前节点内核对适用的前置条件：完整输入和原始授权证据可读，本节点已确定的 design_doc / workspace / review base / 内容快照一致，所需 validation 已完成且有效；Panel / Planreview 不要求尚未产生的实现 workspace、baseline 或代码测试。复审还须确认本轮范围内全部有效 blocking findings 已合批处理。缺项时先补齐，不把已知未就绪的材料交给 reviewer；这不是额外审查或确认门，也不能代替完整 review。尚未调用不占 attempt，实际调用后失败仍占预算。

仅对同一 Gate、同一 reviewer 身份（Panel 使用固定编号 1–4）和同一快照去重：已有进行中的 review 时读取原任务，已有该 Gate 完整且有效的通过证据时按原节点退出条件推进，不因恢复会话或重复总结再开一轮。不同 Panel reviewer 仍独立执行，不能因问题相同而合并或复用彼此结果，Panel 结果不能替代适用的 Planreview，Planreview 不能替代 Deepreview；简单链路的 `not-applicable` 不是 Panel 代替 Planreview 的通过证据。内容、base、scope、实现授权依据或依赖语义变化，或覆盖/证据不足时不得沿用通过结果；需要新 review 时只复用仍有效的参考输入，按对应 Gate 完整重审，不沿用旧 verdict。用户明确要求的新审查和项目强制检查照常执行。

## Human Confirmation Gate

仅在所选链路的确认点或触发停止条件时：

1. 报告当前节点、产物路径、关键决策或 findings、实际验证和未决风险；
2. 说明下一节点及其将执行的动作；
3. 将状态标记为 `awaiting_user_confirmation`；
4. 明确询问用户是否进入下一节点，然后停止。

只有用户在看到本节点结果后明确回复“继续”“确认”“进入下一环节”或同等含义，才可推进。用户要求修改时留在当前节点，
修改完成后重新经过确认 gate。等待期间不得预启动下一节点的 subagents、编辑下一节点文件、调用下一节点 skill 或把下一节点写成已开始。

上下文恢复时先按 Progress Checkpoint 恢复最后一个已获用户批准的节点；证据不清时保持 `awaiting_user_confirmation`，不要猜测。

## Progress Checkpoint

由主 agent 在已有 `control_doc` 或 workflow/review artifact 中维护一个简短的 `Devflow Progress` 块，并在交接摘要中给出其路径。选定位置后更新同一块，不复制历史日志或完整 findings；尚无合适 artifact 时先保留在交接摘要，首个合适 artifact 生成后迁入，不另建状态文件，也不写入设计真源。

Progress 块使用以下固定字段；字段值必须来自当前证据，不用摘要覆盖原批准记录：

```yaml
### Devflow Progress
workflow_version: 1
workflow_path: null  # simple | full；只记录用户已确认的选择
path_approval_ref: null  # 链路选择及后续切换的原文引用
current_node: Brainstorm
status: in_progress  # awaiting_user_confirmation | blocked | completed
next_action: "尚未完成的下一动作"
approved_scope_ref: "原始批准记录及后续明确授权变更的位置"
design_doc: "路径或 null"
implementation_workspace: "路径或 null"
review_base: "ref 或 commit 或 null"
content_revision: "对应证据的版本或 hash（含未提交改动）"
planreview_round: 0
deepreview_round: 0
in_flight: []  # 进行中调用的 handle / job id
evidence_paths: []  # artifact / validation
blocking_findings: []  # 未关闭 finding / blocker 的引用及 owner
```

旧 checkpoint 缺少链路字段时，若原始记录明确表明已在完整链路中，则保留其现有授权与进度；否则读取用户选择依据，无法确定时询问，不凭推荐补填。

仅在节点/评审轮次边界、明确暂停、授权或内容版本变化时更新。`next_action` 必须是尚未完成的动作；等待用户确认时记录待进入的节点，不得记成已获授权。

原始批准的 goal / non-goals / scope / success signals 及可回读的确认原文引用只保存一处，由 `approved_scope_ref` 指向；后续明确授权的变更记录差异和授权依据，不以最新版设计覆盖原始批准记录，slice 和交接只引用该记录。

review 调用前登记该次轮次和 `in-flight`，返回后更新结果；失败尝试同样占预算。恢复时先读 checkpoint，核对授权依据、相关内容版本和证据，再只读取下一动作所需材料；已完成且证据仍有效的节点和 validation 不重跑，review 轮次不归零。未完成调用先查询原任务状态，不重复派发；发现内容变化或证据不足时只重验受影响部分，但完整 review 的范围要求不变。

## Agent Handoff

所有原生 subagent 和 DSH Crew 派发统一使用当前节点所需的最小自包含 brief：

- 所选链路、当前节点/职责、已批准目标、非目标、success signals 和本次范围；
- `design_doc`、workspace、review base / 快照，以及所需文件和证据的可访问路径；
- 文件 ownership / 只读边界、required validation、完成条件及需要停下交还主 agent 的条件；
- 本节点要求的返回格式、artifact 路径（如需产出），以及禁止越界和执行 Devflow 范围外的交付或生产操作。

不附整段会话历史、重复设计全文、无关阶段报告或重复日志。原生派发支持历史继承控制时，默认不继承完整会话（如 `fork_turns="none"`），由自包含 brief 补齐必要约束。需要写文件的 worker 必须知道还有其他改动者，不得回退他人修改。路径不可访问时补齐必要原文；材料不足不得猜测。

返回摘要只给 status / verdict、关键 findings / blockers、validation 摘要和 artifact / evidence 路径；完整 findings 和证据保留在本节点要求的 artifact 中，只读 Panel 无 artifact 时仍按下文格式返回完整 findings。只精简交接文本，不缩减评审范围，不以摘要代替完整设计/改动重审；Panel reviewer 仍互不读取结论。主 agent 读取所需 artifact 和真实 diff/证据后裁决。

## Tool Output and Waiting

- 可预期的大量研发验证或评审输出留在现有日志/临时 artifact，记录命令、内容版本、执行环境、退出码、检查项及适用的成功/失败/跳过计数和证据路径；会话只返回本次变化、失败摘要和必要片段。失败时按线索读取原始 stdout/stderr，不能只看最后几行或摘要就认定根因/通过；管道必须保留被验证命令的退出码，不用日志尾部命令的成功覆盖失败。
- 精简输出不精简输入证据：审查所需源码、diff、授权原文和 findings 必须完整可访问；单次输出会截断时分段读取，不能以截断内容或摘要算已覆盖。日志存储/脱敏沿用项目约定，完整证据仅保留一份并引用，不反复回传相同日志。
- 异步任务登记原 handle / job id，优先用工具原生完成通知、增量游标或等待接口；仍需轮询时先等约 30 秒，无变化退避到约 60 秒（遵守工具上限）。不要用立即查询循环或持续唤醒模型实现等待；接口支持时只取新增输出，否则比较状态且不反复回传相同内容；最终仍读取工具提供的终态、退出码（如有）和完整结果，运行状态不代表成功。
- 观察超时或临时查询失败不能证明任务停止：继续核验同一 handle，不重新派发。只有确认原任务已终止或不存在后才按原重试预算处理。任务有变化、需要干预或用户询问时及时报告；等待期间按宿主要求简短更新，不重复无变化日志或阻塞用户输入。

## 1. Brainstorm

确认以下内容：

- goal、motivation、success signals；
- non-goals 和 scope boundary；
- 当前事实、约束和未知项；
- 候选方案及主要 trade-offs。

只有存在真实取舍时才列多个方案，通常不超过三个。推荐满足目标的最小方案，并说明为什么更复杂方案暂时不需要。
同时按 Path Selection 给出链路建议和依据，进入 `awaiting_user_confirmation`。用户确认选定方案、scope 和链路后，才进入 Save Design；可在同一次答复完成这些确认。

## 2. Save Design

在 `options-monitor` 仓库且 `$om-doc-hygiene` 可用时应用它：

1. 读取 `docs/INDEX.md` 并找到当前 canonical owner；
2. owner 已存在时更新它；仅在没有合适 owner 时创建设计文档；
3. 保留事实、权限、状态、副作用、失败语义和生产安全边界；
4. 不把 `docs/plans/`、`docs/reviews/` 或 `docs/gateflow/` 误当成 living documentation。

其它仓库或 `$om-doc-hygiene` fallback 遵循目标仓库的文档约定完成同样的 owner-first 写入，并明确说明未调用该 skill。

简单链路可在同一个 `design_doc` 中用短段落或表格表达，不要求长篇备选方案或额外计划文件；四位 reviewer 仍须获得完整必要事实，不用聊天摘要代替设计。两条链路的设计文档至少包含：

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

设计首次落盘后，派发四个只读 reviewers：前三个为原生 subagents，第四个由主会话直接调用 DSH Crew。四者使用相同的自包含 brief，读取同一个完整 `design_doc` 快照及目标、约束和事实材料，各自独立回答同一个问题：

> Any suggestions to improve this design?

不预分配架构、安全、简化或对抗角色，也不给 DSH 额外的找茬目标。每位 reviewer 自行判断整份设计最值得改进之处；不得读取其他 reviewer 的结论、主 agent 的预设改法或继承含这些内容的会话，不得编辑文件。建议须遵守已批准 scope contract；没有有价值的改进时可以明确回答无建议并说明依据，不为凑数制造问题。

第四个 reviewer 启动前先检查当前主会话是否提供全局 DSH Crew `dsh_spawn_worker` 或 `dsh_run_worker`。可用时必须由主会话直接调用，设置 `tier=flash`；可并行时优先 `dsh_spawn_worker`，分批执行时可用 `dsh_run_worker`，只读并行任务才可设置 `allow_concurrent_cwd=true`。使用 spawn 后必须通过 `dsh_worker_result` 取得最终结果，不得把 job id 或运行状态当成 review。不得先 spawn `ds-pro` / `ds-flash` Codex subagent 代为调用；当前 Codex 子代理不继承主会话的 DSH Crew MCP tools。

DSH 使用上述相同问题和材料，brief 必须自包含：给出 `design_doc` 和仓库绝对路径、只读边界、验收标准、禁止修改/commit/push，并要求区分直接证据与假设。

容量允许时四者并行；并发槽不足时可分批，但后启动者仍只接收同一原始快照，不得看到先完成者的结论。DSH Crew 不可用、被禁用或确认未创建任务时，用第四个原生 subagent 独立回答同一问题，不减少 reviewer 数量；dispatch 状态不明或结果读取失败时，先按 Tool Output and Waiting 核验原任务/实际派发记录，确认未创建、已终止或不存在且无可用结果后才用该 reviewer 的只读 fallback，临时观察失败不重复派发。不得为运行本节点自动安装、启动或配置 DSH Crew。

汇总时报告 `dsh_crew_status=used|fallback:<reason>`、`reviewer_backend`、`reviewer_model` 和 `independence`。`reviewer_model` 只记录实际结果中可验证的模型身份，否则写 `unknown`；只有证据表明 reviewer 与主 agent 属于不同模型家族时，`independence` 才能写 `verified`，否则写 `unverified`，原生 fallback 写 `native-fallback`。

每个 reviewer 返回建议（或有依据的无建议结论），并说明未覆盖区域；每条建议包含：

- 建议修改的文档位置；
- 具体问题或改进场景；
- 直接证据或明确标记的假设；
- 建议改法、收益、代价和优先级。

主 agent 对输出去重、核验证据并裁决为 `accepted`、`rejected-with-reason`、
`deferred-with-owner` 或 `needs-more-evidence`。不以多数票代替证据判断，不因建议只由一人提出就丢弃；不要把四份输出直接拼进设计文档。

如果当前环境没有 subagent 能力，围绕同一问题自行审查并明确披露无法提供四份独立结果；不要假装执行了并行评审。

任一 reviewer 返回 `review-unusable` 时，不计入四人覆盖；对该 reviewer 最多重试一次或改用回答同一问题的只读 fallback。仍不可用时报告 coverage gap，进入 `awaiting_user_confirmation`，不得进入 Improve Design。

汇总建议、证据和拟议裁决后进入 `awaiting_user_confirmation`；此节点不得直接改设计文档。

- 完整链路：用户确认 accepted 建议后，进入 Improve Design。
- 简单链路：先完成下文只读 Workspace Isolation Check，同时展示拟采纳改法、修改后的预期行为、验收方式、workspace 决策，以及接下来将连续完成设计更新、实现、验证、Deepreview 和 Closeout；请求用户合并确认。仅确认建议而未授权实现时，可以更新设计，但必须在实施前补齐实现授权。项目强制 Planreview 时在后续工作中明确列出。

若仍有影响实现的 `needs-more-evidence` 或未决策略问题，先补齐证据并裁决，不请求含糊的实现授权；新事实影响链路建议时按 Path Selection 处理。

## 4. Improve Design

把 accepted 建议合并回同一个 `design_doc`。在 `options-monitor` 中再次应用可用的 `$om-doc-hygiene`；fallback 时遵循目标仓库文档约定，确保改写后仍是 current-state 文档，而不是评审会话记录。

结构性改动本身不触发额外并行复核。只有存在明确且尚未覆盖的专项问题时，才追加对应职责的 reviewer，并说明问题、现有覆盖缺口及预期证据；不重开完整 Panel，不替代适用的 Planreview。

- 完整链路或项目强制要求：进入 Planreview Gate，普通 blocking finding 按有界循环回写同一个 `design_doc`。
- 简单链路且 Planreview 不适用：核对采纳项已落实、无未决 blocking finding、设计与批准 scope/改法一致，然后冻结设计。已有覆盖该设计和 workspace 的实现授权且前置条件仍有效时直接 Implementation；否则报告差异并补齐所需决定或授权。不得把简单链路作为绕过已出现缺陷的理由。

## 5. Planreview Gate

仅完整链路或项目强制要求时，对最终 `design_doc` 调用可用的 `$planreview`；fallback 时由主 agent 执行 Capability Check 中定义的同等 review。简单链路且无强制要求时跳过本 Gate，记为 `not-applicable`。

要求 `planreview` 检查每个 design decision、slice 和 validation 的 goal alignment，以及 slice 是否按可验证行为切分、是否可以合并；不得把 contract 外的改进机会升级为当前实现要求。

按 Review Completion Rule 使用独立的 Planreview 预算：

1. 对已选方向内的 blocking finding 做最小设计修正，更新同一个 `design_doc`；在 `options-monitor` 中继续应用可用的 `$om-doc-hygiene`。
2. 修正后对完整 `design_doc` 再次调用 `$planreview`，不得只审刚改的章节。

finding 若要求重新选择 goal/non-goals、产品方向或行为、scope、public contract、schema、architecture/owner、安全/权限边界或不可逆副作用，停止自动改进并请求用户决策；需要新的外部或生产授权时同样暂停。循环不得替用户做策略选择或扩大授权。

Planreview Gate 只负责 adversarial review；设计修改仍由主 agent 完成，并继续遵守可用的 `$om-doc-hygiene` 或其 fallback。
适用的 Planreview 未通过时不得进入 Implementation。通过后冻结设计；完整链路执行 Workspace Isolation Check 并请求实现授权。简单链路若合并授权仍覆盖修订后的设计和 workspace，可继续实现，否则报告差异并补齐授权。

## Workspace Isolation Check

两条链路请求 Implementation 授权前，都先做只读检查；完整链路在 Planreview 通过后执行，简单链路在 Panel 汇总时执行：

共享或受保护分支、无关改动及并行冲突的隔离条件优先于任何复用条件；当前或已有专用 worktree 也必须满足隔离条件，干净的受保护 `main` 不例外。满足条件的现有专用 worktree 仍优先于新建。

1. 读取项目 worktree 约定、`git status --short --branch`、`git worktree list --porcelain` 和预期 base；
2. 已处于本任务专用 worktree 时直接复用，不创建嵌套 worktree；
3. 已有 base 和任务范围匹配的专用 worktree 时优先复用；
4. 当前 checkout 仅包含本任务改动且不与其他工作共享时继续使用；
5. 当前 checkout 位于共享或受保护分支、包含无关改动，或并行实现可能冲突时，拟定从已验证 base 创建隔离 worktree；
6. base、worktree owner 或未提交改动归属不清时保持 `awaiting_user_confirmation`，不得猜测。

此检查只产生 `implementation_workspace`、`review_base` 和拟议动作，不创建 worktree、不切分支、不 stash、不移动文件。
将 workspace 决策与当前 Panel 或 Planreview 结果一并报告，在对应确认点取得实现授权。用户明确批准后才执行 workspace 变更，进入 Implementation。

## 6. Implementation

进入 Implementation 后先执行已批准的 workspace 决策，不再增加确认门：

- 复用当前或现有专用 worktree；只有只读检查判定需要隔离时才新建；
- 不自动 stash、reset、移动或清理无关改动；若需迁移，只迁移已核验的本任务文件，并确保目标 worktree 可读取同一个 `design_doc`；
- 实际 base 漂移、目标 worktree 被占用或批准条件不再成立时立即暂停；
- Implementation、validation 和 Deepreview 使用同一 `implementation_workspace` 和 `review_base`。

### Implementation Scope Drift Guard

进入 Implementation 时，在现有 workflow context 中记录 `implementation_baseline`，不创建新的 repository 状态文件。baseline 包含冻结的 `design_doc`、`implementation_workspace`、`review_base`、`HEAD`、`git status --short`，以及每个既有 staged index、unstaged working-tree 和 untracked 内容各自的 hash 和 size；只记录路径不够。该初始 baseline 保持不变，不得用后续检查结果覆盖。

每个 slice 开始前明确对应的 approved success signal、本 slice 交付的行为、expected owners / files 和 validation 命令。
每项实际修改必须归类为：

- `planned`：冻结设计已经要求；
- `required-correctness/safety`：能回答“不做这项额外改动，哪项已批准验收会失败，或已批准行为会在哪条具体路径上不安全？”，并有失败测试或直接代码路径支持。只对额外改动在现有记录中留一句必要性理由及证据引用；正常计划内改动不重复论证。

邻近 cleanup、风格调整、顺手重构、future-proofing、额外监控以及 reviewer 建议本身，都不构成
`required-correctness/safety`。

每个 slice 完成后及进入 Deepreview 前，完整枚举相对 `review_base` 的 committed、staged、unstaged 和 untracked 改动，核对新增、删除、重命名及状态变化；不得只检查已有路径。范围判断始终对照初始 `implementation_baseline` 和冻结 scope。

最近成功检查的文件指纹（各状态层的 hash、size、类型和模式）、范围归类及证据引用保留在现有 workflow context。仅在同一上下文中原文与证据仍完整可用、相关 base / scope / 依赖语义未变且指纹一致时，跳过正文重读；否则重新读取实际内容并归类，删除/重命名须核对前后差异。二进制或过大文件先核对指纹，必要时读取；证据不足不得视为已覆盖。此优化仅用于实现阶段 inventory，不替代 Deepreview 对全部当前改动的完整走读。

无法映射到上述两类的修改不得进入下一 slice：仅属于本 agent 的改动应移除；有价值的发现记录为 `deferred-with-owner`；归属不明或确需改变 scope contract 时暂停并请求用户确认。

Review finding 不是扩大实现范围的授权。只有阻塞 approved success signal 或证明当前实现存在 correctness/safety 缺陷的 finding 才能进入当前修复循环。

### Implementation Model Routing

模型路由不增加人工确认门；主 agent 始终负责设计一致性、集成、validation 和 Deepreview。

Implementation slice 同时满足以下条件时，若当前原生 subagent 支持目标模型，优先使用
`model=gpt-5.6-luna`、`reasoning_effort=max`：

- 冻结设计已经明确行为和实现方向，不需要 worker 做新的设计决策；
- scope、owner、验收标准和测试命令清晰；
- 改动局部、可独立验证，失败后可以安全回退；
- 不涉及 public contract、schema、architecture/owner、权限/安全、并发/状态机、migration、数据完整性或不可逆副作用。

Implementation 委派沿用 Agent Handoff，并明确本 slice 的预期行为。

主 agent 必须核对实际 diff 和测试证据。Luna 结果未通过验收、需要跨越上述边界或出现新的策略性选择时，立即收回主 agent
处理，不让 worker 自主扩大范围。目标模型或 subagent 不可用时直接由主 agent 实现，不阻塞流程。所有改动仍进入相同的完整
validation 和 Deepreview；不得因为使用 Luna 降低验收标准。

按冻结设计的 slices 连续实现。slice 是执行和进度报告单位，不是确认门：

- 复用现有 owner、helper、标准库和已安装依赖；
- 修改最少文件，不为假设性 future work 抽象；
- 从真实入口追踪完整调用链，bug fix 落在共同 root owner；
- 每个 slice 只运行能证明当前行为的最小针对性测试；全部 slices 完成后，对最终内容运行一次项目要求的完整 validation；
- 普通实现取舍、可修复的编译或测试失败不暂停；诊断、修复并继续下一 slice；
- 实现事实与设计记录不一致但不改变策略时，可在同一个 `design_doc` 补充事实和实现细节后继续；不得为迁就实现改写已批准目标、非目标或验收标准，也不得削弱测试掩盖偏离。真正的范围变更须有明确用户授权并记入原始批准记录的变更依据；
- 只有实现需要改变 goal/non-goals、产品行为、public contract、schema、architecture/owner、安全或权限边界、不可逆副作用，或需要新的用户授权时，才暂停并返回相应设计/确认节点。

相同内容版本且证据仍有效的 validation 不重复运行；相关源码、测试、配置、依赖或验证环境变化导致证据失效，或项目/用户要求新验证时重新运行。每个 slice 完成后简要报告 changed files、验证和偏差，随后直接继续下一 slice，不进入 `awaiting_user_confirmation`。全部 slices 和项目要求的 validation 完成后，报告汇总结果并直接调用 `$deepreview`，无需等待用户确认。

## 7. Deepreview Gate

实现和 validation 完成后，对正确 base 下的全部当前改动调用可用的 `$deepreview`；fallback 时由主 agent 执行 Capability Check 中定义的同等 review。

每轮 review 复用并核对 Scope Drift Guard 的当前 inventory，向 reviewer 显式传递本任务的完整文件清单，包括已提交差异、staged、unstaged 和 untracked 新文件；与实际状态不符时先刷新。要求逐个读取纳入范围的新文件实际内容，不能用普通 `git diff` 代替。artifact 必须记录覆盖范围和未覆盖文件/原因；有影响结论的覆盖缺口时标记为 `review-unusable`。此要求同样适用于 companion skill 和 fallback，不靠自动 stage 新文件补齐范围。

同一轮 review 必须读取原始批准记录及后续明确授权的变更，核对每项验收的实现/测试证据，以及新增行为的授权或必要性证据；不能仅凭最新版设计与代码一致就通过。结果复用现有 artifact 和 Closeout 引用，不另开评审、不在每个 slice 重读设计全文或重跑完整 review。

Deepreview 各轮仅在同一审查上下文中，相关批准记录和冻结设计的版本未变且完整原文仍可用时，复用原文继续核对，免于重复工具读取；新 reviewer、上下文压缩、版本变化或证据不足时重读相关原文。只复用参考输入，不复用评审结论，不用摘要替代依据；代码改动仍每轮完整重审。

按 Review Completion Rule 使用独立的 Deepreview 预算：

1. 先完成本轮范围内全部 blocking findings 的共同 root owner 最小修复及针对性测试，再对修复后的内容运行一次项目要求的完整 validation；不逐条 finding 重跑全套。验证失败则修复并重验，不能沿用已失效的结果。
2. 修复后使用同一个 `implementation_workspace` 和 `review_base` 对全部当前改动再次调用 `$deepreview`，不得只审刚修的文件。

finding 若要求改变已冻结的 goal、产品行为、架构、public contract、schema、安全/权限边界或不可逆副作用，停止自动修复，请用户决定范围/方案，并按 Path Selection 重新评估链路；批准后回到 Improve Design 和适用的 Planreview Gate；需要 destructive、外部写入、生产操作或新授权时同样暂停。循环不得绕过这些边界。

实现或修复导致 living docs 变化时，在 `options-monitor` 中用可用的 `$om-doc-hygiene` 更新同一个 owner，fallback 时遵循目标仓库文档约定。所有 blocking finding 关闭并获得可用 verdict 后，报告每轮 artifact、修复和 validation，随后直接进入 Closeout，无需增加确认门。

## 8. Closeout

最终只报告：

- 所选链路、`design_doc` 路径、四人 Panel 结果引用和 planreview 结论（不适用时明确写 `not-applicable`）；
- 实现范围与 changed files；
- validation 命令和结果；
- deepreview artifact 与最终 finding 状态；
- residual risks、owner 和下一步；
- 未执行的 commit / push / merge / release / deploy 边界。

简单链路在全部适用退出条件通过并交代结果后标记为 `completed`，无需额外“完成”确认。完整链路报告后进入 `awaiting_user_confirmation`，只有用户明确回复“完成”或同等含义才标记为 `completed`。两者均不包含 Delivery 或生产操作授权。

## Additional Stop Conditions

以下情况也必须暂停：

- 需要用户在会显著改变行为或范围的方案间选择；
- 权威事实、文件 owner 或目标 base 无法确定；
- 需要 destructive、外部写入、生产操作或新的授权；
- validation 无法运行，且没有等价证据；
- finding 无法安全修复或 residual risk 无 owner。
