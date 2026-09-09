# 全局 Skills 清单与本机分发

## 目标与范围

中央仓库是唯一编辑源；增加一份全局清单、一个同步脚本。create-skill 创建或安装完成后更新清单并同步。采用直接 rsync，适用于本机串行维护。

- 源码：/Volumes/liuxie的硬盘/workspace/agent-skills/skills。
- Codex 全局副本：~/.agents/skills，真实目录。
- Claude 入口：~/.claude/skills，整目录软链到 Codex 全局副本。
- ~/.codex/skills 的系统/运行时内容保持原状。
- 当前分发23项、15手动/8自动；doc、pdf、ponytail 留在源码。首次迁移时为21项。
- 不做远端、项目清单、后台监听、版本发布或 AGENTS.md 扩充。

## 当前事实

首次分发设计时为24项源码和两条源码软链；该迁移已经完成。2026-09-09当前为26项源码、23项全局成员；~/.agents/skills 为真实同步目录，Claude 链接该副本，DSH 默认直接发现该副本。HEAD 为 d81d44332fa377eff7f8e6e78a422af1de40de55；wait-what 安装及其 README、清单、来源、发现记录尚未提交，必须保留。下文“首次迁移”及原始两增量为已完成历史设计，本次只实施末尾的跨工具策略增量。

## 文件职责

| 内容 | 唯一负责人 |
|---|---|
| Skill 内容与调用策略 | 中央 skills/<name>/；Codex策略为决策依据，SKILL.md 表达同一策略供 DSH/Claude 读取，冲突报错 |
| 全局成员 | global-skills.txt，一行一个目录名 |
| 同步 | sync.py，调用本机已安装的 rsync |
| 来源和校验历史 | 现有 migration.json、discovery-verification.json |
| 使用说明和检查 | 现有 README.md、verify_migration.py |

初始全局成员：baoyu-design、create-skill、deepreview、devflow、eli5、find-skills、gateflow、gh-address-comments、gh-fix-ci、grilling、hatch-pet、herdr、ima-skill、kimi-webbridge、phaseflow、planreview、playwright、prdflow、py-perf-analyzer、screenshot、show-me。

## 同步行为

1. 默认 python3 sync.py 只预览；python3 sync.py --apply 执行。源码由中央脚本所在位置确定，目标固定为 ~/.agents/skills。
2. 校验清单和路径后，以 rsync 直接更新真实全局目录。保留文件内容、可执行位，删除不再分发的文件和 Skill。筛选规则必须覆盖整个选中目录，并让未选成员退出副本；本机已验证的参数为 -acvi --delete --delete-excluded，配合每个选中名称的 --include=/<name>/*** 和最后 --exclude=*。-c 防止同大小同mtime的内容差异被跳过；预览加 -n。参数通过数组传递，清单名称只允许小写英文字母、数字和连字符，避免筛选通配符注入。
3. 清单允许空行、整行注释；拒绝空清单、重复、越界名称、缺失源码和无效 SKILL.md。复用已安装 PyYAML 校验 frontmatter；拒绝源内软链和特殊文件。
4. 源码未挂载、目标或父路径异常时先停止。普通同步拒绝软链目标；删除范围只能是已确认专用于本仓库分发的 ~/.agents/skills，不能落到源码、HOME、~/.agents 或 ~/.codex/skills。普通 apply 还要求 Claude 入口为指向该真实目标的软链；这与固定路径检查共同识别约定的新拓扑，拒绝旧布局和未知拓扑，不增加接管参数或状态文件。
5. 使用参数数组调用 rsync，不拼 shell。预览显示新增、更新、删除，不建临时副本、锁或状态文件。默认预览遇两个入口均精确指向源码的旧布局时，只报告一次性迁移步骤及清单所列待复制内容，不调用 rsync 跟随旧链接。新拓扑使用 rsync -n 预览；其它拓扑报错。复制任何非零退出均报失败；成功后检查清单成员及内容/权限与源码一致。
6. 全局副本允许被源码覆盖，不承载独立编辑。更新失败可能留下部分更新；源头完整时修复原因后重新运行同步。没有自动回滚、事务日志、发布收据、版本目录或长期备份轮换。

本机维护按串行操作进行，不承诺并发创建/安装的一致性；create-skill 不并行修改清单和来源记录。同步期间不修改源码。需要多人或并发维护时再引入共享锁，不建设并发发布协议。

## 首次迁移

首次迁移是一次性受控操作，不塞进日常脚本的恢复状态机。实施时先验证两旧链接精确指向中央源码，记录其链接文本，再移走并保留旧链接作为一次性备份；创建真实 Codex 目录，并将 Claude 链接改到 Codex，使入口满足普通同步的前置条件，再执行同步。只操作链接对象，不能沿链接删除源码。

遇失败先报告实际阶段；可通过重新同步完成，或由当前任务按已记录旧链接恢复入口。中途退出后重新核对现场再处理，不宣称脚本会自动恢复。未知文件保留，不能猜测删除。实际迁移在实现授权及临时环境测试通过后执行。

## create-skill 与现有检查

修改 skills/create-skill/SKILL.md：直接使用本机已确定的中央路径，并验证挂载及源码文件；不从运行副本父目录推断，不引入来源收据。临时测试显式绑定测试源码，禁止缺失时回退到真实中央目录。

创建/安装仍复用系统 creator/installer，只写中央源码。内容校验后，重新读取全局清单并加入新能力，更新本次来源/哈希记录，然后运行 sync.py --apply，最后检查实际加载。仅保存源码时不加入；更新已有 Skill 保持其清单归属和调用策略。失败说明“源码已保存，同步未完成，副本可能部分更新”。

verify_migration.py 分别检查源码记录、清单、运行副本及入口。清单是有效源码子集，运行成员精确等于清单；调用方式从 YAML 得出，历史记录不能变成第二套启用配置。保留三个停用项的现有配置，仅检查实际扫描是否报错。README 说明修改源头、预览、执行、失败重试和首次迁移方式。

## 实现与验收

两个行为增量：
1. 清单驱动的直接同步：一个小测试文件覆盖新增/更新/移除、内容和可执行位、重复执行无变化、预览零写入、错误路径拒绝、旧布局只读预览、未知拓扑拒绝、复制失败报错及重跑收敛；包含同大小同mtime异内容用例。测试限临时目录，验证筛选和删除范围不误伤源码或兄弟目录。
2. 创建/安装闭环和首次迁移：更新 create-skill、校验器及现有说明，完成真实预览后迁移。核对24项源码、21项副本、Claude软链、系统目录和其他配置未变；Codex扫描零错误、13手动/8自动，devflow显式加载、planreview/deepreview自动可用，phaseflow可读取gateflow。

不为测试安装无用真实 Skill，不执行上游脚本，不新增测试框架。GitHub下载复用既有安装器，本次只验证安装完成后的分发行为。

## 接受的限制

直接同步不提供全局目录原子切换；读者可能看到更新中的副本。失败后重跑，不保证旧副本完整保留。手工改动副本会被覆盖或删除，因此编辑始终在中央源码完成。首次迁移可能短暂影响入口，旧链接备份用于人工恢复。


## 跨工具调用策略一致性（2026-09-09，本次待实现）

### 目标、边界与验收

补齐同一中央 Skill 在 Codex 和 DSH/Claude 的手动/自动语义。保留现有23项分发成员、15手动/8自动分类和既有正文、UI元数据、依赖；只为 create-skill 调整维护说明。Claude 识别共享字段，手动策略一并对齐。

不新增策略清单、分发目录、脚本框架、后台监听或 AGENTS.md 规则；不改系统校验器，不适配各 Skill 的宿主专属工具/正文，不修改系统或插件缓存，不执行 commit/push/release/deploy。migration.json 分类是验收证据，不作为运行时第三套配置。

成功信号：S1 两端23项分类一致为15手动/8自动；S2 策略冲突或非法值在 rsync 之前拒绝，目标内容不变；S3 创建/安装/更新流程维护两种表达，兼容校验不漏掉其它格式错误；S4 devflow手动启动、planreview/deepreview自动可加载，phaseflow能够读取gateflow规则；S5 wait-what既有安装、其它Skill正文、UI元数据及分发拓扑保持。

### 当前直接证据

sync.py:load_selection 已由预览、apply和 verify_migration 共用，只验证名称/描述；verify_migration 仅解析 openai.yaml。DSH本机 FileSystemSkillProvider 已从 ~/.agents/skills 成功发现并读取23项，零警告；DSH不解析 openai.yaml，只从 SKILL.md 的 disable-model-invocation 计算模型可调用性，目前22自动/1手动。wait-what已自带两种一致的手动字段，其余14个Codex手动入口缺少 DSH 字段。

系统 quick_validate.py 的允许字段没有 disable-model-invocation，且遇未知字段会提前返回，不能仅忽略退出状态就声称其它校验通过。DSH 手动触发是 /name，Codex 为 $name；不要求二者触发文本相同。

### 所选方案与单一职责

1. 继续用每个Skill的 agents/openai.yaml 决定当前本机策略，缺省 allow_implicit_invocation 为 true；SKILL.md 的 disable-model-invocation 缺省 false。有效值须为 YAML 布尔值；本机写入一律 true/false。DSH可接受某些字符串/数字形式，但中央选择更窄的布尔契约并明确拒绝这些非规范形式，不默默转换。两者逻辑互反才一致。冲突只报告Skill路径、字段和当前值，不在同步时猜测、覆盖或生成字段。
2. 在 sync.py 的现有 frontmatter解析旁加入最小共享策略检查，供 load_selection 和 verify_migration 复用；读取原始YAML结构并拒绝重复键（含嵌套policy）、非法映射和非布尔策略值；在兼容副本归一化之前完成此检查。只读取目标字段，保留interface、dependencies等兄弟字段；不能限制顶层只有policy。对待分发成员在任何rsync前检查；未选3项不因本次迁移被启用或改写。完整verify继续验证来源哈希及实际副本，分类使用同一解析结果，避免两份判定实现。
3. 按Codex已确定的15手动分类，为缺少字段的14项 SKILL.md 补 disable-model-invocation: true；wait-what不动。自动8项保持默认，尤其 planreview/deepreview。不批量重写整个YAML或正文。更新本次受影响文件的哈希及本地调整原因，其它哈希保持原样。
4. create-skill步骤4明确写入配对字段：手动为openai allow_implicit_invocation=false和frontmatter disable-model-invocation=true；自动为前者true/省略和后者false/省略。更新已有入口时保留模式和成员归属；上游冲突先核对既有策略/用户选择，不能用下载到的默认值覆盖已明确的本机策略。源头检查通过才调用现有sync；同步后的原生发现/加载仍作为独立证据。
5. 在现有 verify_migration.py 提供面向单个Skill的最小校验入口 --skill <directory>，复用系统 quick_validate.py；create-skill步骤6明确改用该入口，替换对实际源文件的直接系统quick_validate调用。先解析并验证实际源文件的策略，再以临时目录中的 SKILL.md 校验副本移除已验证的 disable-model-invocation 字段，调用未修改的系统校验器检查剩余frontmatter和原正文。仅处理这个已知扩展，不过滤其它未知字段，不匹配或吞掉系统报错文本；系统脚本缺失/调用失败/其它错误均失败。源码保持原样，临时目录自动清理，报告“扩展策略检查+系统兼容副本检查”而非声称系统直接支持原文件。现有完整verify不强制对所有第三方正文新增系统校验规则。

不选择同步时自动转换字段：那会让副本字节与源头不同，破坏现有精确哈希验证。也不新建统一策略文件或生成器：没有需要第三种表示的场景。

### 数据流与失败行为

中央Skill两种字段 -> load_selection策略一致性检查 -> 原有rsync按清单分发 -> 内容/权限验证 -> Codex和DSH分别发现加载。预览也检查策略；无效输入在目标写入前返回失败。复制中故障仍采用现有“可能部分更新、修复后重跑”语义，不增加事务或回滚。新旧策略混合的迁移在源码一次补齐和预检后才执行真实同步。

create-skill 的单Skill校验由实际Skill路径驱动，临时校验仅存必需的SKILL.md，不调用上游脚本；测试路径显式绑定临时源码，禁止回退到真实中央或全局路径。工具不可用时记录未验证项，不冒充加载通过。

### 一个可交付行为增量

跨工具一致性维护与分发（S1–S5）作为一个增量：兼容校验入口与create-skill双字段/步骤6规范先就绪，再完成共享解析、14项元数据和对应哈希更新；整组完成并通过临时测试/源码预检前，不同步或交付半成品。单个源码编辑中间态可失败，不新增事务状态或回滚机制。

测试覆盖手动/自动/缺省、双向冲突、非法值及原始YAML重复键；preview/apply错误用例同时断言rsync调用次数为零和目标快照不变。复用原有rsync路径/重试测试。兼容校验测试覆盖已知扩展有效、其它非法字段/正文不被掩盖、系统脚本缺失或执行失败；后两种用mock/显式临时依赖路径，不动真实系统脚本。创建/更新结果→策略校验→清单→同步→完整校验闭环仅使用临时目录。最后真实预览、同步及两端发现/加载，更新README和已有证据记录。

### 验证计划与限度

使用 /Users/liuxie/.pyenv/versions/3.12.13/bin/python3。运行 test_sync.py、verify_migration.py --source-only、针对受影响Skill的兼容校验、sync.py预览及 --apply、完整verify。相同内容版本通过的检查不重复跑。注入错误用临时目录，不改真实全局做失败测试。

调用Codex原生skills/list确认23项、零扫描错误和15/8策略；临时只读显式加载devflow/create-skill，确认planreview/deepreview默认可用及规则可读取。使用当前已安装DSH FileSystemSkillProvider扫描/加载同一全局目录，验证15项 modelInvocable=false且userInvocable=true、8项modelInvocable=true；检查其真实工具层手动入口/自动loader路径，覆盖devflow、planreview、deepreview及phaseflow/gateflow。若未连接运行中的Web会话，只报告本机provider/loader验收，不称已验证运行中会话或执行完整研发工作流。

已知风险：第三方更新可能覆盖本地字段，以来源记录和同步前检查拦截；Claude手动策略随共享文件改变是已批准范围，但本次不执行完整Claude工作流；临时校验副本只解决一个已知扩展字段，未来扩展应单独评估，不自动放宽。剩余风险owner为中央Skills维护者。
