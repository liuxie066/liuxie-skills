---
disable-model-invocation: true
name: devflow
description: "研发工作流及五个可独立调用的节点：Brainstorm、Save Design、Improve Design、Impl、Review。支持从已有设计或改动进入；完整流程先建议简单或完整链路，由用户选择，两者都保留四路并行设计优化。仅研发，不含提交、发布或部署。"
---

# Devflow

对外只有五个节点：`Brainstorm → Save Design → Improve Design → Impl → Review`。
节点负责自己的输入和产物，workflow 负责顺序、授权和返工；不另建五套 skill。
设计优先，把关键决策和失败语义在实现前说清，不把“90% 设计、10% 实现”变成固定时间配额。

## 调用与编排

- **单节点**：例如 `$devflow Save Design，把已确认方案保存到 docs/design.md`、`$devflow Improve Design docs/design.md`、`$devflow Impl，按已批准设计实现`、`$devflow Review --base main`。明确只做某一步时记为 `mode=node`；完成该节点即停止，不自动启动下一节点。节点名使用上面的五个名称，大小写/自然语言同义说法均可识别；Implementation 映射 Impl，Deepreview 映射 Review。
- **整条或明确组合**：例如 `$devflow 走完整研发流程`、`$devflow 从现有设计开始，优化后实现并审查`。记为 `mode=workflow`，列出本次授权的节点序列；只有 workflow 可以衔接节点。仅说“用 devflow”时先澄清任务并建议路径，不猜已经获得实现授权。
- 先检查当前节点必要输入。已有完整、有效且可回读的输入可直接使用，不为补节点名重跑 Brainstorm/Save Design；输入缺失时只补缺项，涉及其它节点的写操作先确认，不静默扩大单节点任务。PRD 交接只是证据输入，不能虚构前序节点已经执行或通过。
- 原子化指职责与授权边界，不承诺文件操作具备数据库事务。每个节点报告产物、实际验证、未决项和退出状态；输出文件存在不等于节点通过。

### 简单 / 完整预设

两个预设复用同一套五节点及质量规则，都包含 Improve Design 内的四路 Panel；不能为了简单而减少 reviewer。已有输入对应的前序工作只核验，不重复执行。

- `simple`：适合行为清晰、局部、可独立验证的任务；设计可简短，合并展示范围与后续动作，不要求长篇备选方案。
- `full`：适合重要设计取舍、跨系统契约、schema/migration、权限、并发/状态机、交易/账本、幂等或恢复行为变化；充分展示决策、失败场景和验收，再请用户确认实现。文件数量或仅位于这些模块中不单独构成理由。
- workflow 先基于源码事实给出建议、依据、节点序列、所需内部检查及差别，最终由用户选择。没有答复或选择含糊不代表接受推荐；已明确选择则不重复确认。单节点不强制选择 simple/full。
- Planreview 是 Improve Design 的按需内部检查：项目/用户要求，或仍有重要设计风险需对抗性验证时使用，并说明具体原因；不因 full 标签固定加一轮。两个预设均不豁免项目强制检查。
- 发现新事实影响路径建议时说明影响并让用户决定，不自动切换。切换保留有效证据及 review 计数，不绕过未关闭缺陷或失败检查。

### 决策与返工

只在目标/范围、重要产品或设计取舍、实现授权及新的副作用边界上等待确认；已有明确授权在原范围内持续有效，不为节点完成或普通修复重复确认。等待期间不得提前执行依赖该决定的节点。

workflow 中，已确认的目标与范围可进入 Save Design，再进入 Improve Design。完成设计优化后展示实际设计版本、关键决策、验收及 workspace 决策；仅在已有授权覆盖这些输入时进入 Impl，否则请求实现授权。已授权的 Impl 完成后进入 Review。最终报告即收尾，不要求再回复“完成”。

Review 只审查，不改业务代码或设计；问题交由 workflow 返回责任节点：实现缺陷回 Impl，设计缺口回 Improve Design，目标/范围变化回 Brainstorm。授权范围内的普通实现修复合批完成后验证并重审；策略或权限变化先询问。单独 Review 只报告 findings 和建议下一节点，不自动修复或重启全流程。

## 节点契约

| 节点 | 必要输入 | 输出与退出条件 |
| --- | --- | --- |
| Brainstorm | 需求、相关现状、约束 | 目标、非目标、范围、验收、取舍及未决项；必要决定已确认 |
| Save Design | 已确认目标/方案、可回读的依据、保存目标 | 唯一 design_doc 及快照引用，决策和验收可独立阅读；涉既有设计复用时含复用清单（不新增概念、名称或实现时记 `not-applicable`）；缺失选择不得代填 |
| Improve Design | design_doc 快照、目标/边界、事实、允许的设计写入范围 | 四份独立建议、主 agent 裁决、更新后的同一设计及版本；无未决 blocking finding，适用内部检查通过 |
| Impl | 已批准设计版本、实现授权、workspace/base、验收 | 范围内改动、验证证据及 scope 检查通过；单节点到此停止 |
| Review | 正确 base 下完整改动、目标/设计依据、可用验证证据 | review artifact、覆盖、verdict、findings 与风险；无 blocking finding 且证据充分才通过 |

Review 可检查已有改动，即使尚无正式设计文档；以真实需求/授权记录核对已知行为，并明确设计一致性及验证的覆盖缺口，不伪造设计批准、不替用户创建方案。缺口影响结论时保持未通过。

## 共用边界与证据

- 读取适用 AGENTS.md 和当前节点相关源码、配置、测试及文档；只加载当前节点需要的 companion skill。Impl 使用可用 ponytail（已激活不重复初始化）；Improve Design 仅在内部检查适用时加载 planreview；Review 使用 deepreview。OM 设计/实现涉及文档时使用可用 om-doc-hygiene，其余按仓库 owner 约定。
- companion 缺失记 `fallback:unavailable`，主 agent 执行同等必要检查和 artifact 要求；不适用记 `not-applicable`，不得伪称 pass。不自动安装或配置工具。
- 原始 goal、non-goals、scope、success signals、本次授权的实现范围（对应 design_doc 中本次实际授权的 slice/块及各自成功标准）和用户确认依据构成 scope contract，只落盘一处：`<worktree>/.devflow/scope.md`（git 跟踪，随提交同步）。已有 `codex/<task>-devflow-handoff.md`、`docs/gateflow/<task>/scope.md` 或 prdflow 交接的 `prd_doc` 只作为交接输入，进入时把仍有效的授权、范围、产品决定与 design_ref 迁入该文件，不并行维护两份。产品合同（prd_doc）与实现设计（design_doc）各自用 `prd_doc_ref` / `design_ref` 绑定路径加内容 hash；无产品合同的纯实现任务记 `not-applicable`。后续真实授权在该文件追加差异和引用，不能用新版设计或新版 PRD 覆盖原始批准。建议本身不是范围授权；范围外建议记 `deferred-with-owner`。
- 设计与实现绑定 `design_ref`：仓库路径加实际内容 hash，已有固定 commit/permalink 时一并引用；Impl 和 Review 核对同一版本。不得仅引用可变 main 链接。方案决策、理由及相关验收留在唯一设计 owner，避免 v2/final 副本。
- 研发结束时向 Delivery 交接 design_ref、实现及 review 证据。用户另行授权提交/PR时，建议将设计随提交保存，或在 PR 附本次版本的固定链接；无可访问链接时如实提供路径/hash，不编造 URL。
- commit/push/PR/merge/release/upgrade 及生产操作不属于这五个节点；已有旧交付授权不自动覆盖新的研发变更。

## Review 完成与重试

有效且未关闭的严重、高、中问题是 blocking finding。调用失败、输出缺失/无法解析/矛盾、材料截断或覆盖不足均为 `review-unusable`，不得当成无问题或通过。低风险不为清零而扩展范围，保留 owner、影响及后续去向。

Improve Design 的四人 Panel 必须有四个可用结果；无建议但有依据的结果可用。适用的 Planreview 和 Review/Deepreview 各自最多五次调用尝试（含失败），分别计数；第 5 次仍未通过时停下，未经明确授权不得第 6 次。返回责任节点修复、路径切换或上下文恢复不清零计数。

重审前由对应责任节点合批处理本轮范围内全部有效 blockers，完成所需验证，核对快照/base/授权和材料可读性；未就绪不派发，未调用不占尝试。Planreview 在 Improve Design 内对完整修订设计重审；Review 对全部当前改动重审，不只审修复文件。单节点 Review 无修复授权时只交回结果。

去重仅限同一检查、同一 reviewer 身份和同一有效快照。恢复时读取原 in-flight handle，不重复派发；内容/base/scope/依赖或验证环境变化时核验失效部分。四位 Panel reviewer 不能共用彼此结论，Panel 不能替代适用 Planreview 或 Review。仅复用仍有效的完整参考输入和检查证据，不用旧 verdict 代替变更后的重审。

## 进度与交接

scope contract、进度、`implementation_baseline` 与 inventory 指纹共用一个 `.devflow/scope.md`（上文），字段如下；conversation-only 结果不足以替代，不得只在交接摘要里留存。只在节点/内部检查边界、授权或内容变化时更新同一文件：

```yaml
# —— scope contract（原始批准，只此一处；授权差异见下方 authorization_diffs，不覆盖本段）——
goal: null
non_goals: []
scope: null
success_signals: []           # 有 PRD 时逐项溯源到 prd_doc 对应验收（章节/ID）；无 PRD 记 not-applicable
authorized_slices: []          # [{slice, design_doc_ref, success_signal, depends_on}]；success_signal 逐项列出本 slice 覆盖的验收，depends_on 列前序 slice；未授权块 deferred
slice_checkpoints: []          # [{slice, diff_fingerprint, validation, done}]；每片完成时落一条边界快照（可回退、可 bisect）
user_confirmation: []          # 用户确认原话/依据；转述不编造时间戳或消息 ID

# —— product & design & workspace 绑定（Impl/Review 核对同一版本）——
prd_doc: null                  # 产品合同（prdflow 交接的 PRD）路径；纯实现任务无产品需求记 not-applicable
prd_doc_ref: null              # 路径 + 内容 hash；有固定 commit/permalink 时一并引用，不引用可变 main
design_doc: null
design_ref: null               # 路径 + 内容 hash；有固定 commit/permalink 时一并引用，不引用可变 main
implementation_workspace: null
review_base: null

# —— 授权差异（追加；覆盖记录在 scope contract 之外，不覆盖原始批准）——
authorization_diffs: []        # [{when, what, ref}]

# —— 进度 ——
workflow_version: 2
mode: node                     # node | workflow
workflow_path: null            # simple | full；单节点不适用
node_sequence: []              # 只列本次授权节点
current_node: null
internal_step: null            # Panel | Revise | Planreview 等；不是独立外部节点
status: in_progress            # awaiting_user_confirmation | blocked | completed
next_action: "实际尚未完成的动作"
approved_scope_ref: null
path_approval_ref: null

# —— implementation_baseline（进入 Impl 时冻结，不得覆盖）——
implementation_baseline:
  design_doc: null
  implementation_workspace: null
  review_base: null
  head: null
  git_status: null             # git status --short 快照
  staged: []                   # [{path, hash, size}]
  unstaged: []                 # [{path, hash, size}]
  untracked: []                # [{path, hash, size}]

# —— 实现阶段 inventory / 指纹（随检查更新；不替代 Deepreview 完整走读）——
inventory: []                  # [{path, status, hash, size, type, mode, classification, evidence_ref}]

# —— 检查预算、飞行中与证据 ——
content_revision: null
planreview_round: 0
deepreview_round: 0
in_flight: []
evidence_paths: []
blocking_findings: []
```

恢复旧记录时，把 Parallel Design Panel/Planreview 映射到 Improve Design 的相应内部步骤、Implementation 映射 Impl、Deepreview 映射 Review、Closeout 映射结果报告；保留原授权、计数和未完成动作。已通过的 Panel 不因名称变化重跑；原明确等待的用户决定不能被迁移跳过。mode/路径无法从原记录确定时询问，不猜授权。

派发只带当前节点所需的自包含目标、非目标、scope、success signals、design_ref、workspace/base、证据路径、ownership/只读边界、验收与返回格式。原生支持时用 fork_turns=none；不复制整段会话/日志，不让 reviewer 读其他结论。写入 worker 须知道并保留其他人的改动。主 agent 核对实际 diff/完整 evidence 后裁决。

大量日志保留在已有临时 artifact，会话只返回摘要、真实退出码和证据路径；失败时读取原始堆栈，不能以 tail/tee 的退出码冒充测试成功。长源码/diff 分段完整读取。异步调用优先等待通知或增量输出，无变化约 30–60 秒退避；临时超时不等于终止，不重派，不把运行状态当完成；最终读取完整结果。

## 1. Brainstorm

核对目标、动机、非目标、范围、success signals、事实、未知项和候选取舍。涉及既有设计时，“事实”包含同一语义在现库中已有哪些 owner；复用既有 owner 优先于新建平行的结构、名称或实现，确需新建的留下理由。只在确有取舍时比较方案，推荐满足目标的最小设计。确认重大选择；已有明确依据不重问。单节点交付讨论结论后停止，不自动落盘。workflow 同时按预设规则建议路径，用户确认后才继续。

## 2. Save Design

在 `options-monitor` 仓库且 `$om-doc-hygiene` 可用时应用它：

1. 读取 `docs/INDEX.md` 并找到当前 canonical owner；
2. owner 已存在时更新它；仅在没有合适 owner 时创建设计文档；
3. 复用不限于文档 owner：对本次拟新增或修改的每一项概念、名称和实现，按同一 owner-first 口径给出 `复用 <owner 符号或文档>`、`新增`（附理由）或 `unresolved`。覆盖领域结构（字段、实体、状态与枚举、标识与主键、单位与类型约定）、同一语义的别名，以及同一计算或校验的重复实现；`复用` 必须具名 owner，给不出就不是复用声明。检索只产证据、不下裁定，脚本或自动化输出不替代归属判断。范围限定在与之相关的 canonical owner 与声明点，不开放式探索整个仓库，也不以券商或运行时证据代替；记录实际检索范围、关键词及命中为空的结果。可用 skill 自带的只读扫描器 `scripts/reuse_scan.py` 产出候选证据（声明点清单、同名跨 owner、近义名分组、关键词命中）；它只产证据、不产裁定，并会报告自身的截断范围与未读文件——截断不是“不存在”，脚本不可用时手工检索；候选证据按 owner 聚合读取（owner 名 + 命中数 + 代表性声明点），不逐行展开全部命中，仅在下裁定时定点读对应声明点；
4. 保留事实、权限、状态、副作用、失败语义和生产安全边界；
5. 不把 `docs/plans/`、`docs/reviews/` 或 `docs/gateflow/` 误当成 living documentation。

其它仓库或 `$om-doc-hygiene` fallback 遵循目标仓库的文档约定完成同样的文档与既有设计 owner-first 写入，并明确说明未调用该 skill。

简单链路可在同一个 `design_doc` 中用短段落或表格表达，不要求长篇备选方案或额外计划文件；四位 reviewer 仍须获得完整必要事实，不用聊天摘要代替设计。两条链路的设计文档至少包含：

- goal / non-goals / success signals；
- current facts and constraints；
- 复用清单：本次新增或修改的概念、名称与实现的 owner 归属（`复用 <owner>` / `新增` + 理由 / `unresolved`），以及实际检索范围和为空命中；不新增任何概念、名称或实现的设计记 `not-applicable`，不要求检索；
- chosen design and rejected alternatives；
- affected owners、contracts、data flow、state transitions 和 failure behavior；
- implementation slices；
- validation plan；
- risks and open questions。

implementation slice 必须是可独立验证的行为增量，不按文件、模块或 owner 机械拆分；默认不超过 3 个，超过时先尝试合并，并在 `design_doc` 说明无法合并的原因。每片写明其覆盖的 success signal 与依赖的前序 slice；确需更多片时，在 `design_doc` 给出切片总账（覆盖 + 依赖），保证每个 success signal 都被至少一片覆盖、无 orphan——切片多不是问题，覆盖与依赖没有闭合才是。

记录最终 `design_doc` 路径，后续引用同一 owner 及对应版本。

记录 design_ref，报告文档路径、owner、写入内容及检查结果后，本节点完成。仅 workflow 按已授权序列进入 Improve Design；单独保存不启动 Panel。

## 3. Improve Design

### 四路并行优化建议

进入 Improve Design 后，先绑定本轮设计快照，派发四个只读 reviewers，均为原生 subagents。四者使用相同的自包含 brief，读取同一个完整 `design_doc` 快照及目标、约束和事实材料，各自独立回答同一个问题：

> Any suggestions to improve this design?

不预分配架构、安全、简化或对抗角色，也不预设额外的找茬目标。每位 reviewer 自行判断整份设计最值得改进之处；不得读取其他 reviewer 的结论、主 agent 的预设改法或继承含这些内容的会话，不得编辑文件。建议须遵守已批准 scope contract；没有有价值的改进时可以明确回答无建议并说明依据，不为凑数制造问题。

四者的 brief 必须自包含：给出 `design_doc` 和仓库绝对路径、只读边界、验收标准、禁止修改/commit/push，并要求区分直接证据与假设。

容量允许时四者并行；并发槽不足时可分批，但后启动者仍只接收同一原始快照，不得看到先完成者的结论。dispatch 状态不明或结果读取失败时，先按共用等待规则核验原任务/实际派发记录，确认未创建、已终止或不存在且无可用结果后才用该 reviewer 的只读 fallback，临时观察失败不重复派发。

汇总时报告 `reviewer_backend`（`native-subagent`，无 subagent 能力退化为 `self-review`）、`reviewer_model` 和 `independence`。`reviewer_model` 只记录实际结果中可验证的模型身份，否则写 `unknown`；只有证据表明 reviewer 与主 agent 属于不同模型家族时，`independence` 才能写 `verified`，否则写 `unverified`。

每个 reviewer 返回建议（或有依据的无建议结论），并说明未覆盖区域；每条建议包含：

- 建议修改的文档位置；
- 具体问题或改进场景；
- 直接证据或明确标记的假设；
- 建议改法、收益、代价和优先级。

主 agent 对输出去重、核验证据并裁决为 `accepted`、`rejected-with-reason`、
`deferred-with-owner` 或 `needs-more-evidence`。不以多数票代替证据判断，不因建议只由一人提出就丢弃；不要把四份输出直接拼进设计文档。

如果当前环境没有 subagent 能力，围绕同一问题自行审查并明确披露无法提供四份独立结果；不要假装执行了并行评审。

任一 reviewer 返回 `review-unusable` 时，不计入四人覆盖；对该 reviewer 最多重试一次或改用回答同一问题的只读 fallback。仍不可用时报告 coverage gap，进入 `awaiting_user_confirmation`，不得把 Improve Design 记为完成或进入 Impl。


四位 reviewer 的派发 brief 明确：不自行调用 Planreview 或启动其完整流程，不写 review artifact；只返回本节点规定的独立建议。必要的专项/Planreview 检查由主 agent 在汇总后按实际缺口决定，避免四路各跑一套 Planreview。

### 裁决与修订

主 agent 核验证据并处理 needs-more-evidence；不把四份建议原样拼接。已授权设计优化范围内的改进合批写回同一 design_doc；只读请求只交付建议及裁决，说明设计尚未修订，不冒充完整 Improve Design 已完成。重大取舍或 scope 变化先请用户决定，普通已授权修改不逐条询问。修订引入新的概念、名称或实现时，按同一口径补该项的归属行并刷新 design_ref；已核验且版本未变的项不重复检索。

核对采纳项已落实、目标/验收未被偷换、无未决 blocking finding，更新 design_ref。结构性改动本身不触发再跑完整 Panel；明确尚未覆盖的专项风险才补相应证据或 reviewer，说明原因。原快照四份结果绑定原版本，不能伪称四人审过修改后版本。

### 按需 Planreview

仅项目/用户要求，或剩余重要设计风险需要对抗性检查时，由主 agent 对最终完整 design_doc 使用 planreview（缺失则同等 fallback），说明具体原因；否则记 not-applicable。检查 goal alignment、切片是否按可验证行为拆分、失败语义及验收缺口。按五次预算合批修订后完整重审，不按每条建议加一轮。策略、scope、安全或新权限决定立即暂停。

完成修订及适用检查后冻结设计并报告 design_ref、重要决策、建议裁决、验证和风险，结束 Improve Design。单节点不启动实现；workflow 按实现授权和输入有效性决定是否继续。

## 4. Impl

### Workspace Isolation Check

此只读预检可在 workflow 向 Impl 过渡时或独立 Impl 接收输入时执行，不代表已开始实现；请求实现授权前只读确定 workspace/base；若直接调用 Impl 已有足够授权则核对后继续，不重复确认普通可逆隔离选择。

共享或受保护分支、无关改动及并行冲突的隔离条件优先于任何复用条件；当前或已有专用 worktree 也必须满足隔离条件，干净的受保护 `main` 不例外。满足条件的现有专用 worktree 仍优先于新建。

1. 读取项目 worktree 约定、`git status --short --branch`、`git worktree list --porcelain` 和预期 base。首次确定实现基线前刷新目标 remote 的目标分支（通常为 main），记录实际 SHA、本地与远端 ahead/behind，以及任务分支相对目标的独有提交；新任务从已刷新且核验的远端基线开始。fetch 仅更新远端引用，不切换分支或修改工作区；它是事实预检中允许的元数据更新。离线或刷新失败时明确基线未验证，不能将旧引用称为最新；用户明确指定固定历史基线时保留该选择并说明与交付目标的差异；
2. 已处于本任务专用 worktree 时直接复用，不创建嵌套 worktree；
3. 已有 base 和任务范围匹配的专用 worktree 时优先复用；
4. 当前 checkout 仅包含本任务改动且不与其他工作共享时继续使用；
5. 当前 checkout 位于共享或受保护分支、包含无关改动，或并行实现可能冲突时，拟定从已验证 base 创建隔离 worktree；
6. base、worktree owner 或未提交改动归属不清时保持 `awaiting_user_confirmation`，不得猜测。

对删除、退役或基于“无人调用”的简化，在上述基线核对目标符号的导入、调用、动态注册/字符串、exports 和相关测试，并沿真实入口确认保留 owner；审计记录不能替代当前消费者证据。发现新消费者时保留活跃实现，或按已有授权迁移到现行 owner；涉及产品契约或范围取舍则返回对应节点，不能把问题留到合并前。现有任务基线与交付目标已分叉时，先检查完整待交付 diff 是否夹带无关提交，不以工作区干净代替范围核验，也不自动 rebase 或扩大范围。

此检查只更新上述远端引用并产生 `implementation_workspace`、`review_base` 和拟议动作，不创建 worktree、不切分支、不 stash、不移动文件。
报告 workspace 决策；授权不足才询问，授权充分时执行。不能在 Save Design、Improve Design 或 Review 中提前创建实现 worktree。

进入 Implementation 后先执行已批准的 workspace 决策，不再增加确认门：

- 复用当前或现有专用 worktree；只有只读检查判定需要隔离时才新建；
- 不自动 stash、reset、移动或清理无关改动；若需迁移，只迁移已核验的本任务文件，并确保目标 worktree 可读取同一个 `design_doc`；
- 实际 base 漂移、目标 worktree 被占用或批准条件不再成立时立即暂停；
- Implementation、validation 和 Deepreview 使用同一 `implementation_workspace` 和 `review_base`。

### Implementation Scope Drift Guard

进入 Implementation 时，把 `implementation_baseline` 与本次授权范围一并落盘到 `.devflow/scope.md`，不再只留在 workflow context。baseline 包含冻结的 `design_doc`、`implementation_workspace`、`review_base`、`HEAD`、`git status --short`，以及每个既有 staged index、unstaged working-tree 和 untracked 内容各自的 hash 和 size；只记录路径不够。本次授权范围按切片总账列出 design_doc 中本次实际授权的 slice/块、各自覆盖的 approved success signal 与依赖的前序 slice，未授权的块记 `deferred-with-owner` 或留待后续授权。该初始 baseline 保持不变，不得用后续检查结果覆盖。落盘时做一次闭合核对：只对照 `success_signals` 与 `authorized_slices` 两张表，确认每个 signal 都被至少一片覆盖、每片覆盖到某个 signal、无 orphan；缺口记 uncovered，不得带缺口进入实现。

每个 slice 开始前明确对应的 approved success signal、本 slice 交付的行为、expected owners / files 和 validation 命令；其依赖的前序 slice 须已完成并落边界快照。
每项实际修改必须归类为：

- `planned`：冻结设计已经要求；
- `required-correctness/safety`：能回答“不做这项额外改动，哪项已批准验收会失败，或已批准行为会在哪条具体路径上不安全？”，并有失败测试或直接代码路径支持。只对额外改动在现有记录中留一句必要性理由及证据引用；正常计划内改动不重复论证。

邻近 cleanup、风格调整、顺手重构、future-proofing、额外监控以及 reviewer 建议本身，都不构成
`required-correctness/safety`。

每个 slice 完成后及进入 Deepreview 前，完整枚举相对 `review_base` 的 committed、staged、unstaged 和 untracked 改动，核对新增、删除、重命名及状态变化；不得只检查已有路径。范围判断始终对照初始 `implementation_baseline` 和冻结 scope。该片边界快照（diff 指纹 + 验证结果）落 `slice_checkpoints`，作为可回退、可定位的切片边界。进入 Deepreview 前做最终闭合核对：只对照 `success_signals` 与 `authorized_slices` 两张已落盘的表（不重读 `design_doc`），确认所有 signal 都被覆盖、无 orphan；未闭合的 signal 记 uncovered 并暂停，不得当作已完成。

最近成功检查的文件指纹（各状态层的 hash、size、类型和模式）、范围归类及证据引用保留在 `.devflow/scope.md`。仅在同一上下文中原文与证据仍完整可用、相关 base / scope / 依赖语义未变且指纹一致时，跳过正文重读；否则重新读取实际内容并归类，删除/重命名须核对前后差异。二进制或过大文件先核对指纹，必要时读取；证据不足不得视为已覆盖。此优化仅用于实现阶段 inventory，不替代 Deepreview 对全部当前改动的完整走读。

无法映射到上述两类的修改不得进入下一 slice：仅属于本 agent 的改动应移除；有价值的发现记录为 `deferred-with-owner`；归属不明或确需改变 scope contract 时暂停并请求用户确认。

Review finding 不是扩大实现范围的授权。只有阻塞 approved success signal 或证明当前实现存在 correctness/safety 缺陷的 finding 才能进入当前修复循环。

### Implementation Model Routing

模型路由不增加人工确认门；主 agent 始终负责设计一致性、集成及 validation；后续 Review 仅按已授权节点序列执行。

Implementation slice 同时满足以下条件时，若当前原生 subagent 支持目标模型，优先使用
`model=gpt-5.6-luna`、`reasoning_effort=max`：

- 冻结设计已经明确行为和实现方向，不需要 worker 做新的设计决策；
- scope、owner、验收标准和测试命令清晰；
- 改动局部、可独立验证，失败后可以安全回退；
- 不涉及 public contract、schema、architecture/owner、权限/安全、并发/状态机、migration、数据完整性或不可逆副作用。

Impl 委派沿用共用派发规则，并明确本 slice 的预期行为。

主 agent 必须核对实际 diff 和测试证据。Luna 结果未通过验收、需要跨越上述边界或出现新的策略性选择时，立即收回主 agent
处理，不让 worker 自主扩大范围。目标模型或 subagent 不可用时直接由主 agent 实现，不阻塞流程。所有改动仍接受相同的完整 validation；执行 Review 时覆盖全部改动，不得因为使用 Luna 降低验收标准。

按冻结设计的 slices 连续实现。slice 是执行和进度报告单位，不是确认门：

- 复用现有 owner、helper、标准库和已安装依赖；
- 修改最少文件，不为假设性 future work 抽象；
- 从真实入口追踪完整调用链，bug fix 落在共同 root owner；
- 每个 slice 只运行能证明当前行为的最小针对性测试；全部 slices 完成后，对最终内容运行一次项目要求的完整 validation；
- 普通实现取舍、可修复的编译或测试失败不暂停；诊断、修复并继续下一 slice；
- 实现事实与设计记录不一致但不改变策略时，在实现交接中记录差异；仅在另有设计写入授权时更新同一个 `design_doc` 并刷新 design_ref，否则建议由 Save Design 补录；不得为迁就实现改写已批准目标、非目标或验收标准，也不得削弱测试掩盖偏离。真正的范围变更须有明确用户授权并记入原始批准记录的变更依据；
- 只有实现需要改变 goal/non-goals、产品行为、public contract、schema、architecture/owner、安全或权限边界、不可逆副作用，或需要新的用户授权时，才暂停并返回相应设计/确认节点。

相同内容版本且证据仍有效的 validation 不重复运行；相关源码、测试、配置、依赖或验证环境变化导致证据失效，或项目/用户要求新验证时重新运行。每个 slice 完成后简要报告 changed files、验证和偏差，随后直接继续下一 slice，不进入 `awaiting_user_confirmation`。全部 slices 和项目要求的 validation 完成后报告汇总结果，Impl 节点结束。仅 workflow 在授权序列包含 Review 时继续；单节点不调用 deepreview。

## 5. Review

对正确 review_base 下全部本次改动调用 deepreview；缺失时由主 agent 做同等基于证据的审查。独立调用不要求先运行 Impl，也不自动新增设计或重跑所有验证；先核验已有证据，缺少且影响结论时记录缺口。审查可写 review artifact，不修改代码、测试或设计，不自动 stage 新文件。

核对当前 inventory，显式覆盖 committed、staged、unstaged、untracked 新文件及删除/重命名/模式变化；逐个读取新文件实际内容，普通 git diff 不能替代。artifact 记录覆盖及未覆盖范围，影响结论的缺口记 review-unusable。沿真实入口和调用链检查 contracts、失败路径、测试及设计一致性。有 design_doc/design_ref 依据时，新增或修改的概念、名称与实现必须在复用清单中有对应归属行，且该行可核验：`复用` 声明要有具名 owner，`新增` 理由要说明为何不能复用既有 owner；只有形式行而无依据、或与 diff 不符，记 finding。没有设计依据的独立审查记 `not-applicable` 并说明依据。

读取原始批准记录、真实授权变更、绑定的 design_ref 与 prd_doc_ref（无产品合同时记 not-applicable），核验原验收与新增行为的依据；当前设计/代码/测试一致不能掩盖原范围漂移。同一审查上下文的完整参考原文且版本未变时可复用；新 reviewer、压缩丢原文、设计/授权/PRD 变更时重读。代码修改后的每轮仍完整重审，不沿用上轮 verdict。

返回 artifact、verdict、findings、必要下一节点和证据。发现代码问题建议回 Impl；设计缺口回 Improve Design；目标变化回 Brainstorm。是否执行返工由 workflow 和真实授权决定，Review 自身不修复。没有可用 verdict 或仍有 blocking finding 时不得报告通过；有可用失败结论可以完成一次审查任务，但明确研发未通过。

## 结果与交付引用

每个节点完成后简报自己的产物、验证、退出状态及限制。单节点到此结束；workflow 完成其授权序列且全部所需检查通过后，报告：design_ref/设计决策依据、四人建议及裁决引用（适用时）、实现范围与验证、Review 结论/风险，以及给 Delivery 的设计附件或固定链接依据。不再创建 Closeout 节点或要求机械“完成”确认。

产品/范围取舍未决、权威事实或 base/owner 不明、需 destructive/外部/生产新授权、必要验证无可用证据、finding 无法安全修复时暂停并说明具体缺项，不增加无关节点、不猜测通过。
