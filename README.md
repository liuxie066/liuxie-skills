# Agent Skills

本机唯一 Skill 编辑目录：`/Volumes/liuxie的硬盘/workspace/agent-skills/skills`。`global-skills.txt` 决定分发成员；Codex 的 `~/.agents/skills` 是同步副本，Claude 的 `~/.claude/skills` 整目录软链到它。编辑和同步时硬盘需要保持挂载。

共 24 类 Skills。Codex 通过自身配置停用独立 doc、pdf、ponytail；PDF、Ponytail 使用现有插件，本地 Skill Creator 副本已移除，Codex 使用系统版；Claude 共享目录不再提供此副本。Claude 共享同一份21项副本；doc、pdf、ponytail仅留在源码。

直接修改本仓库，再同步。全局副本中的手工改动会被同步覆盖或删除，不能作为独立编辑入口。系统和插件缓存由宿主管理，不复制进本仓库。Codex 调用策略见下文；Claude 的调用策略未调整。

devflow、prdflow 最初导入自既有 liuxie-skills 工作区；后续调用策略在本仓库维护。该旧工作区及其未跟踪 docs 保留，今后不在旧副本独立编辑；公开发布流程另行处理。

kimi-webbridge 使用官方 2.0.5 包，不含本地截图脚本。详细来源和校验值见 migration.json。历史备份在该文件记录的位置，不属于日常加载路径。

本机分发使用 sync.py；中央仓库保存到私有 GitHub 仓库 https://github.com/liuxie066/liuxie-skills。Git 提交推送与本机分发分开执行，未配置后台监听或远端机器分发。

校验要求 Python 3.11+ 和已安装的 PyYAML。源码预检：`verify_migration.py --source-only`；同步后运行完整 `verify_migration.py`。后续有意修改 Skill 后，快照哈希变化属预期，需要重新建立校验基线。旧软链布局下的 Codex skills/list 曾验证 21 个本地入口启用、3 个停用，PDF/Ponytail 插件及系统 Skill Creator 启用。IMA 两份模块文档已改名为 GUIDE.md 并更新引用，正文保持不变；官网地址移入 metadata。格式校验通过，Codex 扫描零错误，入口与启用状态不变。

Codex 手动调用：devflow, prdflow, phaseflow, gateflow, grilling, eli5, show-me, find-skills, hatch-pet, herdr, kimi-webbridge, create-skill, baoyu-design。对应 `agents/openai.yaml` 设置 `policy.allow_implicit_invocation: false`，通过 `$skill-name` 显式调用。

Codex 自动调用：planreview, deepreview, gh-address-comments, gh-fix-ci, ima-skill, playwright, py-perf-analyzer, screenshot。保留默认自动调用；自动选择不扩大操作授权。

Devflow 手动启动后仍按正文自动衔接 Planreview 和 Deepreview。Phaseflow 读取 Gateflow 规则，二者入口手动调用；所有工作流正文保持不变。

校验脚本使用当前已安装的 PyYAML 读取调用策略。

调用策略验收通过：临时只读 Codex 会话确认 Devflow、Phaseflow 不在默认目录中，但显式引用可加载；Planreview、Deepreview 默认可用且指令可读取；Phaseflow 可读取手动入口 Gateflow 的规则。此验收未执行完整开发流程。证据路径见 discovery-verification.json。

新建、更新或从 GitHub 安装 Skill：显式调用 `$create-skill`，说明用途即可。它按请求复用 Codex 系统版 Skill Creator 或 Skill Installer；GitHub 安装显式指定中央目录为目标，并记录来源，将成果放入本仓库，明确调用策略，校验后更新全局清单及本次记录、执行同步，再检查加载；不扩充 AGENTS.md。新增入口后共 13 个手动、8 个自动。

baoyu-design：从 JimLiu/baoyu-design 的 `skills/baoyu-design` 安装，固定提交 `026d4ea012bdd5cada72ac8cc13f21ba4edf2245`（仓库 package 版本 1.2.0）。197 个上游文件已逐个核对 Git blob 哈希；仅新增 Codex 手动策略及仓库根 MIT LICENSE。使用 `$baoyu-design` 显式启动设计流程，未执行上游脚本或安装额外依赖。

## 日常同步

在中央仓库执行；本机已安装的解释器命令为：

```sh
/Users/liuxie/.pyenv/versions/3.12.13/bin/python3 sync.py
/Users/liuxie/.pyenv/versions/3.12.13/bin/python3 sync.py --apply
/Users/liuxie/.pyenv/versions/3.12.13/bin/python3 verify_migration.py
```

默认仅预览，不改变文件。执行时按清单直接rsync，清理副本中的过期文件和未选Skills；空/无效清单、异常路径或软链目标会被拒绝。名称只允许小写英文字母、数字和连字符，允许空行和整行注释。源和目标内的软链/特殊文件不支持。

按串行方式维护，同步时不要编辑源码。同步失败可能部分更新：修复报错后重跑 `sync.py --apply`。没有事务回滚或后台自动重试。仅存源码的新能力不加入清单，更新已有能力保持原有清单归属。

## 一次性入口迁移

旧布局的两个入口均直接链接源码时，默认预览只列出迁移步骤和成员，`--apply`拒绝沿旧链接写入。先核对两条链接的精确目标并记录文本，将链接对象移到一次性备份，再创建真实 `~/.agents/skills` 和指向它的 `~/.claude/skills`，最后同步和验证。未知拓扑不能直接接管；失败先核对实际阶段，可重跑同步或按记录恢复旧链接。不递归删除链接指向的源目录。

本次实际迁移和验证结果记录在 migration.json、discovery-verification.json 及 docs/reviews/global-skill-distribution-panel.md；原有加载报告保留为历史证据。

新布局验收：Codex扫描零错误，21项全局副本启用；13手动/8自动策略保持。Devflow/Phaseflow/Create Skill显式加载、Planreview/Deepreview默认可用、Phaseflow读取Gateflow均通过。临时目录已验证安装结果→清单→同步→完整校验；未实际执行GitHub下载或完整开发工作流。

## GitHub 备份

远端 `origin` 为 `https://github.com/liuxie066/liuxie-skills.git`，仓库为私有。提交并推送中央仓库保存版本历史；`sync.py` 只更新本机副本，不自动提交或推送。仓库保留原有提交和根许可证，各第三方 Skill 的来源及附带许可证仍保留。
