# 跨工具调用策略：Devflow评审记录

## 原始批准范围

用户请求：“[$devflow] 补齐”。Brainstorm输出：现有15手动/8自动策略对齐；create-skill维护双字段；同步前拒绝冲突和非法值；处理系统校验器未知字段但不忽略其它错误；保留wait-what安装；Claude策略一并对齐，不做正文工具适配。用户随后明确回复“确认”，授权Save Design及自动Parallel Design Panel，未授权Improve Design或Implementation。

Goal、scope、non-goals及success signals以此记录为binding contract：仅补齐上述四项，验收为两端23项15/8一致、错误同步零写入、创建安装规范和校验闭环、devflow→planreview→deepreview调用关系及既有内容保留；不新增配置/分发框架，不扩充AGENTS，不改系统，不自动Git交付或发布。

## Devflow Progress

- current_node: Closeout
- status: completed
- next_action: 无；本次workflow已完成，Git交付另行授权。
- design_doc: docs/designs/global-skill-distribution.md
- design_sha256: 249661161089ee78d470a7d7dc32843f655c96180d729cbe04219e0804e5765d (Improve Design; Panel reviewed prior ed9376a0 snapshot)
- workspace: /Volumes/liuxie的硬盘/workspace/agent-skills
- review_base: HEAD d81d44332fa377eff7f8e6e78a422af1de40de55，加既有wait-what未提交安装；本节点只修改设计和本评审记录。
- content_version: 上述design_sha256；实现源码维持Save Design前内容。
- capability_check: ponytail_status=used; planreview_status=used (round 1 completed); deepreview_status=used (available, not invoked yet); om-doc-hygiene_status=not-applicable。
- Planreview attempts: 1 (pass-with-risks; /root/policy_planreview; docs/reviews/plan-review-20260909-231739.md)
- Deepreview attempts: 2 (round 1 fail/review-usable; round 2 pass-with-risks/review-usable; /root/policy_deepreview; docs/reviews/code-review-20260909-235658.md)
- panel handles: /root/policy_architecture; /root/policy_safety; /root/policy_simplicity; DSH hub-1-mtu870te (tier=pro, deepseek-v4-pro, done/review-usable)
- blockers: 0；用户再次“确认”已授权Implementation及隔离/受控回写。

## Validation evidence

Brainstorm阶段源码预检PASS：26源、23全局、15手动/8自动。DSH已安装provider只读发现/读取23项、零警告，当前22自动/1手动，证据/tmp/dsh-skills-verification.json。待评审设计为上述SHA；原始分发设计及评审是已完成历史，本次不重新审查历史实施的非相关问题。

## Review results

### Architecture / ownership

- status: review-usable; reviewer_backend: native; reviewer_model: unknown; independence: unverified。
- 完整设计SHA一致。核对sync.py、verify_migration.py、test_sync.py、create-skill及元数据；未发现阻塞问题。
- 证据：load_selection处于预览/apply/verify共用链路；14项确缺手动字段，wait-what已有；来源/历史不作为第三套策略；正文调用关系存在，实际运行仍待验收。
- 未覆盖：实现、同步、原生发现和运行时loader行为。

### Failure / safety

- status: review-usable; reviewer_backend: native; reviewer_model: unknown; independence: unverified。
- F1 / 中 / accepted（待用户批准后改设计）：设计86–90、102行须明确拒绝原始frontmatter及openai.yaml重复键。场景为重复disable-model-invocation最后值与Codex一致，PyYAML接受而DSH忽略整个Skill。证据sync.py:61使用safe_load；DSH yaml.parse抛DUPLICATE_KEY，provider:670–673跳过。兼容副本重建YAML还可能掩盖原始重复键。
- 最小改法：共享解析阶段拒绝重复键，再做类型/一致性和兼容校验；临时错误样例证明preview/apply在rsync前拒绝且目标不变。收益是避免同步后Skill失踪；代价是局部解析检查，无新框架。
- 主agent已独立只读复现同一输入：PyYAML返回最后true；DSH实际yaml库报DUPLICATE_KEY。
- 未覆盖：实现、临时清理异常、真实同步及运行中Codex/DSH/Claude会话。

### Simplicity / delivery

- status: review-usable; reviewer_backend: native; reviewer_model: unknown; independence: unverified。
- S1 / 中 / accepted（待用户批准后改设计）：设计102–103行A增量先启用检查并迁移字段，B才补兼容入口和create-skill说明；中间状态现有create-skill第6步必被系统validator拒绝，新建仅写Codex字段又被sync阻断。直接证据create-skill现有15/22行和系统validator40–49行。合并为一个可交付增量，内部先实现兼容校验和维护规范，再补齐字段并同步；只重排已批准内容，不增加机制。
- S2 / 低 / accepted（待用户批准后改设计）：设计102行仅断言目标不变，无法区分先rsync -n后失败。增加既有mock的rsync调用次数为零断言，同时保留目标快照比较。测试开销小，直接证明S2声明。
- 未覆盖：DSH/Claude真实解析、运行会话、系统/插件现场快照及实现正确性。

### DSH Crew adversarial critic

- status: review-usable; dsh_crew_status=used; reviewer_backend=DSH hub; reviewer_model=deepseek-v4-pro; independence=verified（与主agent模型家族不同）。job hub-1-mtu870te 最终done/completed，完整SHA匹配，17工具调用，未修改文件。
- H1 / reviewer高 / accepted合并S1：设计89行双表达要求应明确到create-skill步骤4：手动同时写openai false和frontmatter true，自动写true/省略与false/省略。现有步骤仅写Codex字段会被新预检阻断。收益闭环，代价一句说明；本条已在批准目标内，评审器基于旧代码举例不构成新范围。
- H2 / reviewer高 / accepted合并S1：设计90行兼容入口应明确替换create-skill步骤6的直接系统调用。系统validator40–49行拒绝扩展；代价修改原调用说明，收益避免手动Skill更新必失败。
- M1 / reviewer中 / deferred-with-owner：其它扩展字段如whenToUse/user-invocable/tags/type也可能被系统validator拒绝。当前设计明确仅兼容一个已知字段、其它错误仍失败；py-perf-analyzer等既有字段不在14项迁移范围。普遍兼容性属未来单独授权，owner中央Skills维护者；不会将已知拒绝误报成功。DSH支持某字段不证明Codex系统validator承诺支持它。
- M2 / reviewer中 / rejected-with-reason：建议令selected==manual|automatic以保证历史分类完备。实际modes由每个实际源文件计算，15/8输出由selected计算，不依赖历史记录完整性；S1两端实际集合验收不失覆盖。来源历史可包含清单外源码，强制相等会与源码保留策略耦合；本次不扩大历史schema约束。
- M3 / reviewer中 / accepted合并S1：字段/哈希/解析器中间态会导致预检失败；只在整个增量完成并验收后同步，避免半成品进入副本，不加事务机制。
- L1 / 低 / accepted澄清既有保留契约：精确读取policy.allow_implicit_invocation，容忍interface/dependencies兄弟字段，不剥UI元数据。
- L2 / 低 / accepted记录限制：DSH接受部分字符串/数字布尔，中央仅写/校验YAML布尔；宁可明确拒绝非规范上游值，不静默改变两端策略。
- L3 / 低 / 已由Devflow既有机制覆盖：Implementation前记录staged/unstaged/untracked内容hash及size并隔离；wait-what是已批准安装但本次实现基线中的既有内容，不以普通混合diff代替task inventory。
- 未覆盖：完整Claude工作流、DSH运行时所有根同名遮蔽、user-invocable未来轴、未选3项额外策略交叉、兼容入口缺失系统脚本等未来实现测试。前三项均保持已声明范围；依赖缺失测试按原有失败语义用mock/显式临时路径，不改真实系统。



## Panel结论及继续授权

四个职责均review-usable，设计核心方向保留。共三项去重后拟修改：重复键拒绝；合并可交付增量并明确create-skill双字段/兼容入口；错误用例同时断言rsync未调用与目标不变。

用户在看到主agent汇总的三项修正后再次回复“确认”。该回复授权Improve Design；当时DSH仍在进行，主agent承诺先补齐四人覆盖再推进。DSH最终新增建议经核验与已批准目标/三项修正重合，其它泛化/历史schema建议已按上述理由延后或拒绝，未扩大scope。现四人覆盖齐全，进入Improve Design及自动Planreview；Implementation仍未授权。

Improve Design完成：三项已批准修正已回写同一设计文件；自动进入Planreview第1轮。

## Planreview与Workspace Isolation Check

第1轮review-usable/pass-with-risks，0 material findings；完整报告docs/reviews/plan-review-20260909-231739.md。主agent核对完整报告、设计SHA和证据，设计冻结为249661161089ee78d470a7d7dc32843f655c96180d729cbe04219e0804e5765d。剩余风险：原有部分更新语义、其它扩展字段不支持、未覆盖完整Claude/Web工作流及上游覆盖；owner中央Skills维护者，去向现有Closeout/来源记录，未来需求另立范围。

只读检查：仅一个worktree，位于main，HEAD及本地origin/main同为d81d44332fa377eff7f8e6e78a422af1de40de55。当前脏文件为已知wait-what安装（README、global-skills、migration、discovery与skills/wait-what）和本次设计/评审记录，无现有专用工作树可复用。拟议路径及分支未占用。

Implementation待批准方案：
- implementation_workspace: /Volumes/liuxie的硬盘/workspace/agent-skills-worktrees/cross-tool-invocation
- branch: codex/cross-tool-invocation
- review_base: d81d44332fa377eff7f8e6e78a422af1de40de55 + 创建隔离工作树时核验并复制的既有未提交内容基线（逐文件hash/size；staged/unstaged/untracked分开）。
- 用户批准后创建工作树，将已核验wait-what及设计/评审副本带入，不移动、不stash、不清理中央原件。实现/临时测试/Deepreview在同一工作树，基线包含现有安装，不把它算本次新增实现。
- 只在整组代码/策略/哈希检查通过后，重新比对中央原文件与基线，受控回写本次文件到唯一中央源；若发现漂移暂停，不覆盖。使用中央脚本进行真实分发/发现验收，将证据同步到同一review工作树，以实际内容hash核对两处本次受影响文件一致。Deepreview覆盖整个本次delta和真实验收证据，不以普通HEAD diff吞并既有改动。
- 不自动commit/push/merge/release，不修改系统或插件；此刻没有创建worktree或回写任何实现。

## Implementation baseline

用户“确认”授权本节点。隔离工作树及分支已按批准方案创建；HEAD保持原base。实际基线另含并行prdflow改动，已逐文件保留，不归本次所有。

- implementation_workspace: /Volumes/liuxie的硬盘/workspace/agent-skills-worktrees/cross-tool-invocation
- baseline_evidence: /Users/liuxie/.codex/skill-backups/cross-tool-invocation-20260909-233704/baseline.json；before/包含原始字节与模式，index单独记录。
- slice: S1–S5单一增量；owners=sync.py、verify_migration.py、test_sync.py、14项手动frontmatter（create-skill另更新正文）、migration.json、README.md、discovery-verification.json。其余正文及wait-what字节不变。
- validation: Python 3.12.13 -B test_sync.py；verify_migration.py --source-only/--skill；中央sync预览/apply/full verify；实际Codex发现和DSH provider/tool loader；完整Deepreview。

## Implementation validation

S1–S5整组完成，所有改动planned，无额外实现范围。baseline对比通过，受控回写20文件后同步23全局项，源与全局内容/权限完全一致。既有wait-what与并行prdflow正文/测试逐文件保留；本次仅14个frontmatter和create-skill正文、三个现有脚本、README/manifest/discovery及控制记录变化。

- test_sync.py通过（包括preview/apply错误零rsync调用、目标不变、重复键/非布尔/冲突、未知字段/TODO拒绝、依赖缺失/调用失败及临时清理、安装/更新闭环）。source-only与全局verify通过：26/23，15手动/8自动。
- Codex原生skills/list零错误23项；临时只读会话实际显式注入devflow/create-skill/phaseflow，planreview/deepreview默认可用且读取成功，gateflow规则读取成功。未执行流程。
- DSH已安装provider+registry+tool loader实际函数51/51通过，15手动模型拒绝/8自动可加载，用户/devflow和/phaseflow注入；注册/agent上下文模拟，未验证运行Web缓存及Claude客户端。
- 15手动项兼容校验14通过；eli5原有description含尖括号被系统拒绝。该文本与baseline完全相同、原生发现成功；按S5保留正文及设计“其它错误仍失败”，记录为既有内容限制，owner中央Skills维护者，今后单独更新该Skill时处理。未降低校验。
- evidence_directory: /Users/liuxie/.codex/skill-backups/cross-tool-invocation-20260909-233704
- review_inventory: /Users/liuxie/.codex/skill-backups/cross-tool-invocation-20260909-233704/task-inventory.json；task.patch相对before基线（不吞并既有wait-what/prdflow）。

## Deepreview remediation — round 1

/root/policy_deepreview 返回 docs/reviews/code-review-20260909-235111.md：review-usable/fail，1项中F1。主agent读取完整artifact并accepted：原生Codex日志和目录证实allow_implicit_invocation:no被忽略，而旧PyYAML预检误判False放行。该问题直接阻断S1/S2/S3，属required-correctness，不增加策略或范围。

已修F1：仅本地UniqueKeyLoader采用true/false布尔识别（包括YAML允许的大小写），yes/no/on/off在策略位置成为非法字符串，显式!!bool no也拒绝；保留UI文本On，未修改PyYAML全局解析器。两字段合计22个大小写/别名方向用例、preview/apply零rsync、目标不变及--skill预检覆盖，规范TRUE/False和全局resolver保留断言通过。test_sync.py完整回归通过。README旧Claude策略句已修正。

原生23项均使用规范值，Skills源码未再次变化；先前Codex/DSH实测证据仍对应当前Skill字节，无需重跑模型会话。第二轮仍覆盖完整task delta及新增第1轮artifact，不仅审修复行。

## Closeout

Planreview第1轮pass-with-risks；Deepreview第1轮F1中已accepted并修复，第2轮完整22项delta复审pass-with-risks，0未关闭material finding。报告：docs/reviews/code-review-20260909-235658.md。主agent已读取完整报告并核对最终内容版本，自动进入Closeout。

交付：现有sync.py/verify_migration.py/test_sync.py补共享策略检查、单Skill兼容校验和回归；14项手动frontmatter/create-skill规范及来源/验收记录更新；中央23项同步完成（15手动/8自动），既有wait-what及并行prdflow内容保留。

验证：Python3.12.13 -B test_sync.py完整通过；AST解析通过；source-only/full verify及中央sync preview/apply通过，最终apply无内容变化；Codex原生发现和只读显式加载、DSH实际loader51项通过（具体模拟边界见discovery）。全部本任务文件中央/工作树hash一致；HEAD维持原base，index为空。

Residual owners：中央Skills维护者负责eli5既有尖括号格式（未来单独更新时处理）、宿主会话刷新/完整Claude与DSHWeb工作流（需要时单独验收）、已有串行rsync部分写入限制（失败重跑）。未创建新配置/同步框架，未改系统/插件、AGENTS，未执行Git提交/推送/合并/发布/远端部署。

用户于 2026-09-10T00:09:21.831029+08:00 明确回复“完成”；已按devflow Closeout将workflow标记为completed。未执行Git提交、推送或发布。
