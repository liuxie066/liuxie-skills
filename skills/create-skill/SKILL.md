---
disable-model-invocation: true
name: create-skill
description: "按本机中央仓库约定创建、更新或从 GitHub 安装 Skill，复用 Codex 系统 skill-creator 和 skill-installer，并明确调用策略。通过 $create-skill 显式启动。"
---

# Create Skill

编写复用 Codex 系统版 `skill-creator`，GitHub 安装复用系统版 `skill-installer`，共用以下本机约定。

1. 读取当前可用的系统 `skill-creator/SKILL.md`，使用它的编写规范、初始化工具和校验器；不复制或修改系统 Skill。系统版不可用时报告缺少的依赖，不自动安装替代品。
2. 本机中央仓库固定为 `/Volumes/liuxie的硬盘/workspace/agent-skills`。确认硬盘已挂载，且中央 `sync.py`、`global-skills.txt`、`skills/create-skill/SKILL.md` 存在；不从本文件的父目录推断源码，不在全局副本写入。仓库校验使用 Python 3.11+ 和已有 PyYAML；本机可用 `/Users/liuxie/.pyenv/versions/3.12.13/bin/python3`。临时验收只使用明确指定的测试源码/测试入口；路径缺失即停止，禁止回退到真实中央目录。
3. 本机按串行方式维护，同步时不修改源码。先运行 `verify_migration.py --source-only`，区分已有变化和本次改动；全局副本暂时不同不能阻止修复后重试同步。新建或安装只放到中央 `skills/<name>/`；同名目录存在时先检查，按用户意图复用或更新，不删除重装。实验稿不放入日常源码目录。
4. 新建或安装前明确用途和调用方式，将目录、模式用于本次系统工具操作：
   - 用户明确指定的方式优先。
   - 用户主动启动的工作流入口默认手动：`agents/openai.yaml` 中设置 `policy.allow_implicit_invocation: false`，同时在 `SKILL.md` frontmatter 设置 `disable-model-invocation: true`。
   - 需要模型判断场景的能力，或被其他工作流自动调用的下游能力，保留自动调用：`policy.allow_implicit_invocation: true` 或省略，同时 `disable-model-invocation: false` 或省略。两字段只接受 YAML 布尔值，不接受字符串、数字或重复键。检查调用方后再定；不能仅因包含写操作就设为手动。
   - 更新已有 Skill 时保留其本地策略和清单成员归属，除非用户要求改变；上游更新不得覆盖已选策略。用途不足以确定模式时只询问这个关键点；已有明确约定时不重复确认。
5. 按请求选择分支，保留已有 UI 元数据、依赖和无关内容；不添加共享 `AGENTS.md` 规则。自动选择 Skill 不代表扩大操作授权。
   - **创建或修改内容**：使用系统 `skill-creator`，只编写最少必要的文件。
   - **从 GitHub 安装**：读取系统 `skill-installer/SKILL.md`，明确仓库、仓库内 Skill 路径和 ref。只有仓库链接且存在多个候选时先列出供用户选择，不安装整库。用系统 `scripts/install-skill-from-github.py --repo <owner/repo> --path <skill-path> --ref <ref> --dest <central-root>/skills`；也可用 `--url`，但必须显式指定同一个 `--dest`，不能落到默认的 `~/.codex/skills`。用参数列表或正确的 shell 引号传递路径。目标已存在时核对来源和用户意图，不删除后重装来绕过安装器的冲突检查。
   - 安装保留上游内容，只做已确定的本地调用策略调整；若上游已有不同策略，先核对调用依赖和用户选择。下载不需要执行上游附带的安装脚本。记录仓库、路径、ref（可核实时附 commit）及本地调整，便于以后更新；不把上游仓库当成本机编辑入口。
6. 使用上述解释器执行中央 `verify_migration.py --skill <skill-directory>`：先校验真实源文件的双端策略、布尔类型、重复键及一致性，再在临时 `SKILL.md` 副本中只移除已校验的 `disable-model-invocation` 字段，交给未修改的系统 `quick_validate.py`。原文件不变，其它未知字段、正文错误、系统脚本缺失或运行失败均须失败；这是扩展校验加系统兼容副本校验，不代表系统原生支持该扩展。自编或修改的脚本做最小运行校验；下载来的脚本先阅读，只在任务授权范围内执行验证。此时只验证源码；实际发现与显式调用放到同步成功后。
7. 校验通过后重新读取 `global-skills.txt`：新建或安装 Skill（包括 GitHub 和官方安装包）默认加入全局清单，并同步到 Codex、Claude、Hermes、DSH 和 Pi，避免重复。只有用户在当前安装请求明确指定“仅保存源码”或“仅安装到某宿主”时才缩小范围；不能仅因当前使用 Hermes，或上一任务在同步 Hermes，就把新的安装请求限定到 Hermes。将已有 Skill 同步到指定宿主不改变原有全局成员归属。更新已有 Skill 保留原有成员归属，不重新启用清单外的能力。只更新 `migration.json` 中本次 Skill 的文件哈希、来源、调用分类和数量，记录原因；不重置无关文件的哈希。重新运行 `verify_migration.py --source-only`。
8. 用上述解释器执行中央 `sync.py --apply`，随后运行完整 `verify_migration.py`；检查 Codex `skills/list` 扫描错误、启用成员及必要的手动显式加载/下游可用性，将实际发现证据保存到 `discovery-verification.json` 并更新 README。同步失败时报告“源码已保存，同步未完成，副本可能部分更新”；修复后重跑同步，不回滚新源码、不误报安装完成。工具不可用则明确未验证项；不把文件存在当作加载成功。

9. 默认分发还须完成本次新建/安装 Skill 的宿主接入：DSH 原生读取 `~/.agents/skills`，与 Codex/Claude 共用已同步内容；Pi 在 `~/.pi/agent/skills/<name>` 建立指向 `~/.agents/skills/<name>` 的链接，已有同名内容先检查并备份，不覆盖未知入口；Hermes 先查找已有同名 Skill，无同名时完整复制到 `~/.hermes/skills/imported/<name>`，更新时备份并保留其必要的宿主适配。更新已有 Skill 时同步其已安装宿主。检查各宿主原生发现和加载（Hermes `skills_list`/`skill_view`，Pi 原生 Skills loader，DSH provider/loader）；区分加载验证与业务能力验证，工具不可用如实报告。宿主中没有 Codex API 时用可用的终端/文件工具读取本机系统 Skill，不能假定专有工具存在。保留明确删除/排除项，尤其不得恢复 `screenshot`；不批量启用历史未选技能。

完成时简要给出 Skill 路径、调用方式和验证结果。手动入口在 Codex 用 `$name`，DSH/Claude 用 `/name`；自动下游保留自动策略。调用策略变化时核对 DSH 实际发现/加载结果，不能只以文件字段推断运行时成功。Git 提交推送、发布与远端同步按用户另行授权执行。
