# 全局 Skills 分发：设计四方评审

## Devflow Progress

- current_node: Closeout
- status: completed
- next_action: 无；用户已确认完成。
- workspace: /Volumes/liuxie的硬盘/workspace/agent-skills
- review_base: /Users/liuxie/.codex/skill-backups/global-distribution-20260909-082445/baseline.json及before/原始内容；代码评审范围见review-scope.json。
- design_doc: docs/designs/global-skill-distribution.md
- design_sha256: a8b971a2bbfcd43c998f2fb1582230f62fbebaa8f7c244687bd48530221c655d（R1/R2修正后的轻量设计；下方旧Panel仅对应各自旧快照）
- Planreview attempts: 2
- Deepreview attempts: 1
- panel handles: /root/distribution_architecture; /root/distribution_safety; /root/distribution_simplicity; DSH hub-39-mtst3occ (tier=pro，deepseek-v4-pro，done / review-usable)
- blockers: 无；Deepreview第1轮pass-with-risks，0个未关闭严重/高/中finding。
- capability_check: Ponytail used；Planreview used；Deepreview used；om-doc-hygiene not-applicable。

## 原始批准范围（只在此处保存授权记录）

用户任务：“增加一份全局清单、一个同步脚本。create-skill 完成创建或安装后更新清单并同步”。
用户修正：“主目录在codex”。随后用户确认的方案为：中央源码保持硬盘 workspace/agent-skills/skills；按全局清单同步到真实 ~/.agents/skills；~/.claude/skills 整目录链接过去；~/.codex/skills 保留系统和运行时内容。
本次用户明确回复：“确认”，授权 Save Design 及其自动衔接的 Parallel Design Panel。未授权 Improve Design、Implementation、commit/push/merge/release 或远端分发。

binding scope contract：本机唯一源码＋清单分发＋Codex真实全局副本＋Claude整目录链接；初始保持21项/13手动8自动，3个停用副本留源头；create-skill 更新源码与清单后同步；失败保护旧副本，验证工作流依赖。排除SSH、项目清单、监听、发布及无关Skill修复。

## Evidence

- Save Design 前 verify_migration.py: PASS（24 source skills，13 manual / 8 automatic）。
- 两个全局入口仍直接链接源码；真实入口尚未迁移。
- Git main 无提交；本节点仅新建设计和本评审记录。

## Review results

### Architecture / ownership

- backend: native；model: unknown（未从返回元数据核实）；independence: unverified；review-usable。
- 完整读取设计及 verify_migration.py、README、create-skill；设计 SHA256 一致，未读其他评审。
- A1 / 中：设计第46行通用检查禁止目标解析到源码，与59–61行初始化只接受旧源码软链冲突。当前真实布局满足后者、违反前者。建议把旧入口验证和清理对象验证分开：仅 --init 精确接受旧软链，移动/备份作用于链接对象；新目录及普通同步仍拒绝指向源码。收益：首次迁移可执行且保护源码；代价：少量分支及正反例检查。
- 其他核对：21项与现有调用快照一致；目录名匹配；内容/清单/收据 owner 分离明确；create-skill 的路径与验证顺序问题已纳入；工作流依赖保留。
- 未覆盖：具体事务状态机、崩溃窗口、rsync参数、路径竞态、实际发现、所有Skill的历史硬编码路径；不代表实现验收。

### Failure / safety

- backend: native；model: unknown（未从返回元数据核实）；independence: unverified；review-usable。
- 完整读取同一设计及指定现有源码，SHA256一致，全程只读。
- F1 / 高：46、69–70行只在 sync --apply 内持锁，清单和 migration.json 的读改写在锁外。两个 create-skill 会话基于相同旧清单分别增加项目，后写者丢失前者更新；串行sync也无法补回。建议下载/内容准备完成后，对重新读取并合并清单及相关记录到同步使用同一写入边界，避免嵌套锁；收益防止丢失更新，代价锁职责调整，不需锁网络下载。
- F2 / 高：50–55、61、90行未具体定义提交点、旧收据/Claude原链接保存以及允许的实际拓扑。rename已成功但阶段记录滞后、新收据已替换但尚未提交、回滚自身再次中断时无法可靠判定。建议最小恢复状态表：每次变更前记录旧收据、原链接、旧/新摘要，未提交回滚，提交后仅清理；恢复幂等，测试记录落后与恢复中断。收益使安全承诺可实现；无需版本指针新架构。
- F3 / 中：46行先创建锁再检查父目录。若 ~/.agents 指向其他位置，拒绝前已越界写入；未规定锁文件类型/生命周期。建议先检查父目录，再拒绝锁软链、确认当前用户普通文件；固定锁文件不在退出时删除，关闭fd释放，避免旧/新inode成为两把锁。收益路径安全与可靠互斥，代价很小。
- F4 / 中：同 A1，初始化精确例外应先于通用目标拒绝条件，且仅操作原链接本身。
- 未覆盖：实际rsync参数、实现路径竞态防护、真实中断实验和宿主发现；以上是设计缺口而非已验证漏洞。

### Simplicity / delivery

- backend: native；model: unknown（未从返回元数据核实）；independence: unverified；review-usable。
- 完整读取设计和指定现有源码，SHA256一致，全程只读。
- S1 / 高：40–42行默认命令dry-run零写入，51行“下次执行先恢复”却可能rename/写收据。中断后运行默认命令会冲突。建议pending事务的dry-run只报告恢复计划并非零退出，只有--apply恢复；所有失败阶段增加中断→dry-run无变化→apply恢复的组合检查。收益消除接口冲突，代价一个分支和复用测试场景。
- S2 / 低：28、42、48行全新候选目录复制仅约6.91MiB，shutil.copytree/copy2即可保留当前要求的内容/权限，rsync增加外部依赖。可选用stdlib；新候选无论哪种复制工具都不需要--delete。收益减少依赖分支，代价失去当前未使用的rsync功能。非阻断建议，不应引起恢复架构重设计。
- 两段行为增量合理；锁、收据、恢复对应批准的安全验收，不能为简化删除。无需更多配置或测试平台。
- 未覆盖：收据伪造、完整路径竞态/崩溃安全、真实发现和恢复实验。

### DSH adversarial critic

- dsh_crew_status: used
- reviewer_backend: DSH Crew hub
- reviewer_model: deepseek-v4-pro（最终结果元数据已核实），tier=pro，effort=max
- independence: verified（工具最终模型为 DeepSeek 家族，主会话为 GPT 家族；worker 自报因看不到主会话身份而 unverified，由主会话按双方身份补足）
- job: hub-39-mtst3occ
- session: session-fd21f67e-6c22-4d54-af7c-a8e222240ec9
- status: awaiting_user_confirmation

以下为第四位 reviewer 完整最终返回；其 F1–F10 在主裁决中记为 D1–D10，避免与安全评审编号冲突。

证据核验完毕。所有关键声明均已用现场证据交叉验证，现在交付第四位评审（DSH adversarial critic）的完整结论。

---

# 第四位评审：DSH 跨视角对抗批评（只读）

**快照核验**：SHA256 实测 `7bf5c4cfb61c71f79b76ac371419ed6ca66fabeba4337b9fab12c12279ea5221`，与指定快照一致。全程只读：未写任何文件、未执行同步/安装、未启动 worker、未读取 docs/reviews 中他人结论。

**现场事实核查（直接证据）**：两入口确为指向中央 `skills/` 的绝对软链 ✓；`skills/` 恰 24 项、无软链、无 .git/.DS_Store ✓；`migration.json` 的 `codex_disabled=[doc,pdf,ponytail]`、`invocation_policy` 13 手动/8 自动与设计第 34 行清单精确吻合 ✓；`verify_migration.py` 实测 PASS ✓；git 无 HEAD、全未跟踪 ✓；机器装的是 **openrsync**（protocol 29，非 GNU rsync）；`~/.agents` 已有 Codex 自有的 `.skill-lock.json`；config.toml 中已有 8 条 `~/.agents/skills/paseo-*` 悬空禁用条目（且当前零错误）；源码有 3 个可执行文件（`playwright/scripts/playwright_cli.sh`、`gh-fix-ci/scripts/inspect_pr_checks.py`、`doc/scripts/render_docx.py`，前两个在被分发清单内）；外部卷为 APFS（noowners）。

---

## Findings

### F1【高·严重度 / 高·优先级】中断状态机未定义，且与"无收据真实目录不可接管"规则存在死锁矛盾

**位置**：Apply 流程步骤 5-6（第 50-51 行）、首次入口迁移（第 59-63 行）、收据字段（第 55 行）。

**失败场景**：
1. SIGKILL 落在"候选改名就位"与"原子写入新收据"之间 → 重跑时看到"真实目录 + 旧收据"→ 按第 47 行"无收据的真实目标目录不能被接管"直接停止，需要人工救援 —— 与第 61 行"中断重跑能……完成已验证的布局"的承诺直接矛盾。
2. 在 rsync 构建候选期间崩溃：此时尚未写任何状态（设计只在"移动前"写可恢复状态，第 50 行），旁路临时目录里留下半成品；没有日志记录证明该目录归属，与"不递归清理未知目录"（第 51 行）冲突，重跑既不敢清也不敢用。
3. Claude 链接切换用 unlink+symlink 两步实现时，在两步之间崩溃 → `~/.claude/skills` 消失；恢复需要知道"原始链接目标"，但第 55 行的收据字段清单里没有该字段。

**证据**：设计文本自身的三处矛盾（第 47/51/61 行）；验收第 90 行明确承诺"中断后重跑"可恢复，但全文没有枚举任何事务阶段或转移表。【假设】实现者会自行补全阶段日志——不成立，这是核心安全机制的规格缺口。

**建议改法**：显式定义日志/收据的 `phase` 枚举（`building → verified → swapped → committed`）及每阶段的必要字段（候选路径+哈希、旧目标类型/身份、Claude 原始链接目标、备份路径），并规定**候选构建开始前**先写 `phase=building`；给出每阶段重跑的恢复转移表；追加"恢复过程中再次崩溃"的幂等重试测试（验收第 90 行现缺此项）。
**收益**：验收第 90 行从口号变为可验证行为，消除人工救援死路。**代价**：半页规格 + 3-4 个注入用例，实现量小。

### F2【高·严重度 / 高·优先级】create-skill 的 SKILL.md 重写未被列为交付物；现有文本在 --init 后主动错误

**位置**：create-skill 集成（第 65-71 行）；现文 `skills/create-skill/SKILL.md` 步骤 2-3、7。

**失败场景**：
1. --init 后从全局副本运行 create-skill：现文步骤 2 用"上三级"定位 → 得到 `~/.agents`；且"`~/.agents/skills`、`~/.claude/skills` 均解析到仓库 skills/"的检查按新拓扑必然为假 → 按现文"路径不符时先报告，不另建副本"→ create-skill 死路，新建/安装闭环全断。
2. 验收第 93 行的临时环境闭环测试要求 create-skill 针对临时 source_root 工作；现文第 11 行硬编码 `/Volumes/liuxie的硬盘/workspace/agent-skills`，会导致测试要么失败、要么**写入真实中央目录**——直接违反"不为测试在真实中央目录添加无用示例 Skill"。
3. 现文步骤 7"最后重跑 verify_migration.py"在新顺序（第 70 行：同步后再检查）下会变成"同步前跑含受管副本断言的 verify"→ 必然失败；重排必须写进 SKILL.md 文本。

**证据**：现文 `SKILL.md` 第 11-12 行（上三级推断 + 双软链检查 + 硬编码绝对路径）、第 23 行（verify 重跑位置）为直接证据；设计第 67 行只写"验证中央 sync.py 与 skills/create-skill/SKILL.md"，未要求改写该文件；第 82 行 slice 2 提"路由与顺序"但未点名 SKILL.md 文本。

**建议改法**：把"改写 create-skill SKILL.md 路由段"作为 slice 2 的显式交付物：收据 `source_root` 为主路由，仅初始化前回退到已知中央路径；删除硬编码绝对路径；同一文本必须同时兼容 init 前（软链布局）与 init 后（收据布局）；重排步骤 7 为"源码校验 → sync --apply → 全量 verify"。
**收益**：第 93 行验收与真实 post-init 流程均可实现，临时测试不可能碰真实仓库。**代价**：同 slice 内的小段文档改写，可忽略。

### F3【中·严重度 / 中·优先级】rsync 能力面未按本机实际（openrsync）钉死，存在 GNU 旗标假设

**位置**：第 28 行（"编排已安装 rsync"）、第 36/42/48 行。

**失败场景**：实现者选用 GNU-only 旗标导致首次 `--apply` 失败或行为异常：`-c/--checksum`（本机 help 只有 `--checksum-seed`，无 `--checksum`）、`--info`（本机只有 `--out-format/--itemize-changes`）、`--protect-args`、`-X`（本机是 `--extended-attributes`）；或按 GNU 退出码 23/24 分支（openrsync 语义不同）。另外第 42 行"缺少 rsync 返回非零"无法区分"缺失"与"能力不足"。

**证据**：`rsync --version` 输出 "openrsync: protocol 29 / rsync version 2.6.9 compatible"；`rsync --help` 旗标清单为直接证据。设计自身的内容校验走 Python 侧哈希（步骤 4），恰好在 openrsync 缺 `-c` 时仍可行——但未被钉死。

**建议改法**：规格中写明 rsync 调用契约限定为 openrsync 兼容旗标（`-a`、`--del` 仅限候选目录内、参数列表），内容比对一律 Python 侧哈希；任何非零退出即失败；dry-run 增加一次廉价能力探测（版本 + `-n` 冒烟），区分"缺失/不支持/失败"三种报错。
**收益**：本机首次 --apply 可靠；杜绝 GNU 假设漂移。**代价**：数行探测 + 一个测试。

### F4【中·严重度 / 中·优先级】adapt 后的 verify_migration.py 与 migration.json 的对账不变量未定义

**位置**：第 75 行；职责表第 31 行；migration.json 的 `invocation_policy`/`codex_disabled`。

**失败场景**：手工从 `global-skills.txt` 删名（清单是分发真源，允许）后，adapt 版 verify 若没有"manifest 与 policy 的关系"断言，则要么完全不报（成员漂移静默发生，skills/list 数量变化无人察觉），要么沿用第 26-27 行旧断言导致 create-skill 预检误失败。同理"用户明确只保存源码不加入清单"的新 Skill（第 69 行）不能破坏 `policy == sources − codex_disabled` 旧不变量。

**证据**：现 verify 第 19-20、26-27 行的断言结构；设计第 75 行只说"成员只来自 global-skills.txt"，未规定与 migration.json 的核对关系。【假设】实现者会保留旧不变量并只加清单子集断言——需要钉死。

**建议改法**：在设计中写明三个不变量：`manifest ⊆ sources − codex_disabled`、`policy(manual∪automatic) == sources − codex_disabled`（不变）、manifest 成员逐一有 SKILL.md 且 openai.yaml 与 policy 一致；初始清单由 `sources − codex_disabled` 机械生成并与第 34 行比对（我已核对两者当前精确一致）。
**收益**：成员变更在两份记录间不可能静默分叉。**代价**：三条断言。

### F5【中·严重度 / 中·优先级】受管副本一旦出现任何漂移即全量停摆，且无诊断/补救通道

**位置**：第 47 行（遇手工改动/未知文件停止）、第 89 行（拒绝条件）、第 77 行（README 禁止编辑副本）。

**失败场景**：`~/.agents/skills` 内任一 skill 目录出现运行时产物（某 Skill 自写缓存/状态文件、代理写元数据、Spotlight 写 `.DS_Store` 入子目录）→ 之后**每一次** sync 与 create-skill 预检（跑 verify）全部以"手工改动"停止，且没有任何 `--status/--diff` 能告诉用户是哪个文件、怎么补救（带回源码？删副本文件？），连无关 Skill 的更新也被一并锁死。

**证据**：第 47/89 行文本；【假设】现有 21 个 Skill 都不会写自身目录——当前成立（playwright/hatch-pet/py-perf-analyzer 均写工作区），但设计未将其作为受控前提声明，也未提供发现漂移后的处置路径。

**建议改法**：保留 fail-closed，增加只读 `--status`（或 dry-run 输出）列出与收据不一致的具体路径；README 写明补救规程（"改动带回源码或从副本移除，sync 永不代决"）。白名单机制首版不做、记为后续。
**收益**：可诊断、可解锁，不削弱安全性。**代价**：复用现有比对机制，量小。

### F6【中·严重度 / 中·优先级】步骤 2 校验与步骤 5 替换之间的 TOCTOU 窗口

**位置**：第 47 行（步骤 2）与第 50 行（步骤 5）。

**失败场景**：非协作写者（用户、运行中的 Codex/Claude 进程、Spotlight）在校验通过后、改名替换前修改目标 → 被改动过的树整体移入备份、候选上线；sync 报告"成功"，违背"遇到手工改动时停止"承诺；而该改动只存在于"最多保留上一份"的备份里，下一次 sync 的清理（第 50 行）会把它删掉。

**证据**：设计文本自身——校验在步骤 2、替换在步骤 5，之间无复查；锁（第 46 行）只排除其他 sync.py，不排除任意写者。【假设】只有 sync.py 会写 `~/.agents/skills`——不可执行。

**建议改法**：在 rename 前一刻重算目标内容/权限摘要并比对，不一致即中止并按恢复流程处理（复用步骤 2 的摘要，成本极低；或对目录 inode 做 fstat 绑定检查）。
**收益**：堵住一个真实的数据保全缺口。**代价**：几毫秒哈希。

### F7【低·严重度 / 低·优先级】锁机制未指定（flock vs. 锁文件存在性），且存在既有文件名碰撞

**位置**：第 46 行。

**失败场景**：若实现为 O_CREAT|O_EXCL 锁文件，SIGKILL 留下陈旧锁 → 此后所有 sync 永久拒绝直到人工删除（PID 检查变体有 PID 复用竞态）；若锁名取 `.skill-lock.json`，将撞上 `~/.agents/.skill-lock.json`（现存在，为 Codex 自有文件）。

**证据**：`ls ~/.agents` 实测存在 `.skill-lock.json`；设计未给锁文件命名与机制。

**建议改法**：指定 `fcntl.flock` 非阻塞排他锁、专属路径（如 `~/.agents/.skills-sync.lock`），进程死亡自动释放；忙时给出明确错误；恢复流程绝不删除锁文件。
**收益**：无陈旧锁死路。**代价**：可忽略。

### F8【低·严重度 / 低·优先级】doc/pdf/ponytail 停用配置路径在 init 后悬空，需预设补救分支

**位置**：第 17 行（保留原配置）、验收第 92 行。

**失败场景**：init 后三条 `~/.agents/skills/{doc,pdf,ponytail}/SKILL.md` 路径从"存在"变"不存在"，若 Codex 对"曾被发现后消失"的禁用路径产生告警，真实迁移验收会卡住，而设计除"不改其他全局配置"外无补救分支。**有利反证**：config.toml 第 321-355 行已有 8 条 `~/.agents/skills/paseo-*` 悬空禁用条目且当前 skills/list 零错误——悬空禁用路径被容忍已有直接证据；未覆盖的仅是"发现后移除"这一增量。

**证据**：config.toml 第 321-403 行、README 第 15 行。【假设】"移除后"与"从未存在"被同等容忍——需在真实迁移时确认。

**建议改法**：保持设计不变，但在验收第 92 行旁写明：若出现告警，补救 = 经用户授权后调整 config（移除或改指源码），预先决策而非现场卡住。
**收益**：迁移不会在真实机一步卡死。**代价**：无。

### F9【低·严重度 / 低·优先级】"清单名与 Skill name 相符"校验需要 YAML frontmatter 解析，与"Python 标准库"表述冲突

**位置**：第 28 行（标准库）、第 36 行（名称校验）。

**失败场景**：实现者若恪守"标准库"，用 `^name:` 正则解析 frontmatter——会被 description/正文中的 name 字样、多行/引号名骗过，或干脆跳过该检查弱化"精确成员"验收。

**证据**：`verify_migration.py` 第 6 行已 `import yaml`——PyYAML 本就是本仓库校验链的既有依赖；frontmatter 为 YAML（create-skill SKILL.md 头部为直接样本）。

**建议改法**：二选一并写明：声明 PyYAML 为 sync.py 依赖（与 verify 一致）做真实解析，或把检查降级为结构检查。同时钉死清单解析细节：strip 空白、拒绝行尾注释/CRLF/BOM。
**收益**：确定性校验。**代价**：一行依赖或删一条检查。

### F10【低·严重度 / 低·优先级】一组小规格缺口：无 --init 的 --apply 行为、清理失败语义、退出码契约、收据版本降级

**位置**：第 42-51、63 行。

**失败场景**：(a) 当前软链布局下误跑 `sync.py --apply`（不带 --init）：第 47 行只覆盖"无收据真实目录"，软链目标不是真实目录——应显式拒绝并提示 `--apply --init`；(b) 步骤 5 备份清理失败是否使事务失败未定义——应为提交后尽力而为，永不失败；(c) create-skill 需区分 no-op/已发布/冲突/锁忙/错误的退出码契约未定义；(d) 收据格式版本比 sync.py 新（降级场景）应 fail closed 而非忽略未知字段。

**证据**：设计文本缺口；验收第 89/90 行未覆盖这些情形。

**建议改法**：规格各加一句 + 一个退出码表。**收益**：消除实现歧义。**代价**：微。

---

## 已核实无问题的部分

- 批准范围内的成员/内容/权限验收、dry-run 零写入（第 42 行已正确定义为"不建目录/锁/收据、不改入口"）、重复 no-op（第 49 行）、并发拒绝（第 46 行）、输入错误拒绝（第 36 行）在文档中均有对应条款。
- 非目标未越界：无 SSH、无 project profile、无监听（第 71 行明确"同步只在完成时触发"）、无 Git 发布（第 84 行"不自动创建初始提交"）、不动 `.codex/skills`/系统/插件（第 61 行）、不扩 AGENTS.md。
- 初始 21 项清单与 `sources − codex_disabled` 实测精确一致；13/8 策略与 migration.json、README、verify 输出三方一致。
- "沿链接删除源目录"防护（第 51 行）、`--delete` 仅限候选（第 48 行）、收据路径不被信任（第 55 行）等安全要点设计到位。

## 未覆盖区域

- openrsync 精确旗标组合的实机行为（本评审只读，未执行任何 rsync；留给实现阶段测试）。
- Codex 扫描器对"发现后移除"禁用路径的容忍度（需真实迁移时验证，见 F8）。
- Claude Code 对新链接的实际读取行为；Codex 自有 `.skill-lock.json`/skill-install 机制与 sync 的交互（按非目标排除，未审计）。
- 21 个 SKILL.md 正文内部的路径假设（phaseflow→gateflow 等）：设计第 101 行已声明为后续事项，本评审未全树审读。
- 大规模扩展（>21 项）的性能表现；非 macOS、多用户 home 场景（本机单用户范围外）。
- docs/reviews 其他评审结论：按要求未读取，独立性保持。

## Review 状态

**review-usable**。快照哈希核验通过，所有核心声明均与现场直接证据交叉验证；findings 全部给出设计位置、具体失败场景、证据或明确标注的假设、改法/收益/代价与优先级；无写入、无越界。身份披露：本槽位由主会话直接调用的 DSH worker 承担（本会话模型 deepseek-v4-pro；与主 agent 的模型家族差异无法从内部验证，`independence=unverified`）。**不推进到实施。**



## 主会话去重与裁决

本节仅确定拟采纳项，尚未修改设计或实现。四份结果均 review-usable；Panel 完成不等于设计通过。所有 accepted 项 owner 为主会话，待用户确认后在同一设计中落实并进入 Planreview。设计快照仍为 7bf5c4cfb61c71f79b76ac371419ed6ca66fabeba4337b9fab12c12279ea5221。

| 编号 | 裁决 | 核验与下一步 |
|---|---|---|
| A1 / F4 | accepted | 第46行与59行确实冲突。仅 --init 精确接受当前两个旧源码链接并操作链接对象；普通 apply 拒绝链接并提示初始化。 |
| F1 | accepted | 第69–70行先改记录后调用带锁 sync，不能保护读改写。内容准备后，同一排他写入边界内重新读取/合并清单与本次记录，再发布；避免嵌套锁。同名源内容并发不得以最后写入者获胜，遇基线变化停止。 |
| F2 / D1 | accepted | 最小事务表需覆盖构建开始、旧入口移走、新入口就位、提交、清理；记录旧收据和原 Claude 链接以及对象身份/摘要，阶段日志滞后时以允许的实际拓扑核验。未提交回滚，已提交只清理；恢复优先于普通目标接管校验。候选清理归属在构建前建立，并覆盖恢复再次中断。 |
| F3 / D7 | accepted | 先验证固定父目录，再以非跟随方式打开当前用户普通锁文件，用 fcntl.flock；固定专属 .skills-sync.lock，不删除锁 inode。不得触及已有 .skill-lock.json。 |
| S1 | accepted | dry-run 遇未完成事务只显示恢复需求并非零退出；不写锁/状态/目录。只有 apply 可恢复。 |
| S2 | rejected-with-reason / partially accepted | 不改用 shutil：当前用户采用 rsync 分发方向，工具已安装，保留最小兼容参数即可。采纳其删除多余 --delete 的部分：候选是新目录，无需该参数。 |
| D2 | rejected-with-reason（高严重度）/ accepted（表述澄清） | 第18、67、70、82行已明确修正 create-skill 的路由与顺序，“未列为交付物”不成立；仍在 slice 2 点名 SKILL.md。测试必须使用临时 source_root，路径不匹配即停止，不能回退写真实仓库；仅真实旧布局可使用已知中央路径。 |
| D3 | accepted | 本机为 openrsync 2.6.9 compatible；使用最少兼容选项，Python 侧做摘要比对，任何非零复制退出均失败；实机兼容行为纳入临时目录检查。无需新增 GNU-only 功能。 |
| D4 | accepted（明确不变量）/ rejected-with-reason（建议公式） | verify 确有旧 policy == sources - codex_disabled 断言。新增/移除/仅存源码要各有明确验证，但不把历史 codex_disabled 升格为分发准入规则。成员只由清单决定：清单是有效源码子集，运行副本精确等于清单；调用方式从各自 YAML 得出，migration 中分类仅核对记录快照。初始21项/13手动8自动单独验收，不永久硬编码数量。 |
| D5 | accepted | 复用现有比较结果，在 dry-run/错误中报告具体漂移路径与类型；README 说明由用户把修改带回源或移除副本新增内容后重试。保留 fail-closed；不加 --status、白名单或强制覆盖机制。 |
| D6 | accepted（数据保全） | 发布前复核目标，移动后核对备份，清理前验证备份未漂移；未知修改保留并停止/报告，不能随下一次备份轮换静默删除。单次 rename 前哈希不能消灭所有竞态，不宣称能阻止持有旧文件句柄的任意非协作写者。README 明确副本非编辑入口。 |
| D8 | deferred-with-owner | 当前已有悬空停用条目且扫描成功，仅假设移除后行为不同，未证明需改 config。owner 主会话在真实验收检查；若确有错误，保留证据并按失败恢复规则处理，再请求配置范围授权；本次不预改全局配置。 |
| D9 | accepted（复用 YAML）/ rejected-with-reason（无必要限制） | verify 已依赖 PyYAML，复用 yaml.safe_load 解析 frontmatter 并检查类型/name，不用正则冒充解析；文档应声明既有依赖，无需安装新包。允许常见 CRLF，不增加拒绝 CRLF 等无关限制；清单只允许整行注释的现约定继续适用。 |
| D10 | accepted（最小契约） | 普通 apply 在旧布局明确拒绝；未知收据版本停止；提交后清理失败只报已发布但清理未完成，不回滚已提交数据。退出码只需0成功/no-op、非0未完成，具体原因由文本说明；不建立多码协议表。 |

### 验证、覆盖与边界

- 主会话直接核对设计全文、当前 verify_migration.py 和 create-skill/SKILL.md，对 D2/D4 等意见独立裁决；未机械接受所有建议。
- 三个原生 reviewer 模型元数据不可核实，统一 unknown / unverified；第四位工具最终身份 deepseek-v4-pro，与主会话 GPT 家族不同，independence=verified。
- DSH 最终返回 done，四位均检查同一设计 SHA256；未互读结论。实际分发、崩溃恢复、openrsync 参数组合、Codex 新拓扑发现与工作流调用仍留待实现验收。
- 本节点只保存设计和本评审记录。全局软链未迁移、同步脚本与清单未实现；无 Git 提交/推送、远端操作。
- 当前结论：Panel complete / awaiting_user_confirmation。阻断项是上述 accepted 的高/中设计缺口，尚未回写关闭；并无 review coverage gap。
- 下一步：用户确认 accepted 裁决后进入 Improve Design，再自动执行 Planreview；本次不提前启动。


## 用户要求简化（2026-09-09，当前裁决）

授权依据：主会话提出“清单 + dry-run + 路径保护 + 直接 rsync”，用户回复“我觉得这个不适合做得过重”。依此缩小设计；这是当前节点的修改请求，不是采纳旧评审全部意见或实现授权。

本记录保留原批准范围不改写。当前简化方案明确调整原先“失败保护旧副本”的承诺：原地更新可能部分完成，依靠中央源码重跑收敛；不再承诺事务回滚。已将这个取舍写入同一设计并向用户报告，待确认后继续流程。

旧 A1/F4 路径保护、S1 预览零写入、D3 openrsync兼容、D2 creator路径和顺序、D4验证职责、D9复用YAML解析保留为简化方案要求。F1并发事务锁、F2/D1恢复状态机、F3/D7锁生命周期、D6漂移保护与备份轮换不再是当前目标；D5改为预览差异和失败重跑说明，不保护副本独立编辑；D8真实扫描检查保留；D10仅保留普通错误报告。S2的“新候选无需delete”已不适用，原地更新需要正确处理过期成员和文件。

不重开四方评审，不启动Planreview或实现。原评审全文作为旧快照证据保留，不声称新设计已有四方通过结论。当前只更新设计和此记录。

## 轻量方案确认与 Planreview 授权（2026-09-09）

用户看到轻量方案、失败后部分更新和手工改动会被覆盖的说明，以及“按这个轻量版继续 Planreview 吗？”后回复：“继续”。据此确认替代原事务发布要求的轻量范围，授权 Improve Design 及自动 Planreview，不授权实现或真实迁移。简化设计已在上一节点按用户修改请求写入，本次核对后直接进入完整 Planreview；主会话执行，最多5轮。

## Planreview round 1

artifact: docs/reviews/plan-review-20260909-081058.md；review-usable / fail。R1 checksum重跑收敛、R2首次预览与拓扑识别均accepted，属于已批准行为的必要修正。不恢复事务机制。主会话随后更新同一设计并执行第2轮完整重审。

## Planreview round 2 registration

主会话已将R1/R2最小修正回写同一设计。第2轮in-flight；评审完整设计，SHA256=a8b971a2bbfcd43c998f2fb1582230f62fbebaa8f7c244687bd48530221c655d。两项变化仅规定rsync比较参数、旧/新拓扑预览与一次性迁移顺序，未新增状态文件/后台/锁/回滚机制。

## Planreview round 2 result / workspace decision

artifact: docs/reviews/plan-review-20260909-081352.md；完整重审review-usable / pass-with-risks。R1/R2关闭，0 blocking；设计冻结SHA256=a8b971a2bbfcd43c998f2fb1582230f62fbebaa8f7c244687bd48530221c655d。

Workspace Isolation Check为只读：当前仓库无HEAD、无remote、唯一checkout；源文件与既有迁移快照完整匹配。拟在实现获批后同目录创建任务分支codex/global-skill-sync，保存全部既有文件hash/size/类型作为review_base，不自动提交或构造无基线worktree。当前未切分支、未实现脚本或清单、未迁移入口。

验证解释器：/Users/liuxie/.pyenv/versions/3.12.13/bin/python3（tomllib/PyYAML可用）；原verify PASS。裸python3在本目录为3.9，失败已记录，不改全局环境。

## Implementation authorization and baseline

用户看到实现、测试、本机迁移和自动Deepreview范围后回复“确认”。已在同一checkout创建codex/global-skill-sync，未提交。implementation_workspace=/Volumes/liuxie的硬盘/workspace/agent-skills；review_base=/Users/liuxie/.codex/skill-backups/global-distribution-20260909-082445/baseline.json，原文件副本位于/Users/liuxie/.codex/skill-backups/global-distribution-20260909-082445/before。基线包含原未跟踪内容hash/size/类型、索引、系统Skills和config摘要及旧链接文本。

Slice1 planned owners: global-skills.txt、sync.py、test_sync.py；目标是固定路径按清单直接rsync、预览、错误拒绝和重跑收敛。Slice2 planned owners: skills/create-skill/SKILL.md、verify_migration.py、README.md、migration.json、discovery-verification.json及一次性全局入口迁移。只更新当前必要记录与评审artifact；不改其它Skills内容。

## Slice1 result / Slice2 start

Slice1: global-skills.txt（21项）、sync.py、test_sync.py已实现。临时测试PASS：内容/权限、清单新增移除、同大小同mtime修复、预览无写入、失败重跑、路径/输入拒绝；真实入口尚未改。Slice2正在修正creator、现有校验器和说明；两片均planned，未引入额外平台或状态协议。

## Implementation complete / Deepreview attempt 1

两片planned改动完成，真实入口迁移成功。验证：test_sync.py PASS（临时复制+源码/成员/运行闭环），quick_validate.py create-skill PASS，verify_migration.py --source-only及完整模式PASS；真实dry-run无变更；原生app-server扫描0 errors/21 enabled；只读临时Codex实际加载及工作流依赖PASS。证据目录：/Users/liuxie/.codex/skill-backups/global-distribution-20260909-082445。仅create-skill正文改变，其他Skills源码与基线一致；系统Skills和全局config内容未改。

本次没有执行上游脚本、GitHub下载、完整业务工作流、提交推送或远端同步。现进入Deepreview第1轮in-flight，完整scope由/Users/liuxie/.codex/skill-backups/global-distribution-20260909-082445/review-scope.json列出；基线为同目录baseline.json及before/。

## Deepreview result / Closeout

第1轮完整Deepreview：docs/reviews/code-review-20260909-083955.md，review-usable / pass-with-risks；9/9实现文件覆盖，0 blocking。原生专项reviewer /root/distribution_code_review负责三个Python文件逐行及creator调用链，主会话整合并核对完整范围/原始授权/数据证据。实现版本与review-scope.json匹配。

自动进入Closeout：两个planned增量和真实迁移均完成；测试、源码/副本校验、原生发现、显式入口和下游读取验证均PASS。未执行完整GitHub下载或业务工作流；保留已批准的串行、部分更新和副本可覆盖限制。无源码修复剩余，无Git提交/推送/发布/远端同步。等待用户确认完成。

## Human Confirm Completion

2026-09-09T08:41:04：用户回复“完成”，本轮Devflow标记为completed。无新增代码或配置修改，提交推送及远端同步仍未执行。
