# 项目入口定位

这些是定位提示，不是可直接执行的部署配置。先绑定当前 checkout，重新读取该版本的 `AGENTS.md`、脚本、workflow 和目标环境事实；不从本文件推断授权、主机、安装目录或当前版本。

## Options Monitor (OM)

- 本机源码通常在 `/Volumes/liuxie的硬盘/workspace/options-monitor`。入口约定见 `AGENTS.md`，部署见 `docs/DEPLOY_LINUX_MAC.md`，验证见 `tests/README.md`。
- 版本和发布入口：`VERSION`、`CHANGELOG.md`、`scripts/release_check.py`、`scripts/release_preflight.sh`；CI 查 `.github/workflows/release-from-version.yml`、`release.yml` 和 `_release-reusable.yml`。按当前约定区分 workflow_dispatch 和 tag 触发，避免同时触发重复发布。
- 本地完整发布预检现有入口为 `OM_PYTHON=/absolute/path/to/python bash scripts/release_preflight.sh --full`；解释器、依赖图、元数据和测试门槛以当前脚本为准；使用当前入口的并行参数，不额外重跑一轮串行全量测试。
- 升级复用 `./om update check|apply|verify|rollback`。读当前 CLI 的参数和行为，确认 apply 所需 current symlink 与目标 tag；无 `--confirm` 的 apply 是预览，但仍须核对该版本是否有准备副作用。
- 发布优先沿项目 GitHub Actions 的 VERSION → tag/Release 流程；升级由远端内置升级器消费已核验的 GitHub tag。不要默认上传本地源码归档；确需替代传输时，先明确目的地、载荷和授权。
- 执行升级/回滚前核对 `service.profile.json` 的 `deploy_user` 与有效 UID，以部署用户运行预览和执行；不要用 sudo 包裹整个升级命令。服务操作沿用项目已有的 sudo 路径。当前与目标升级器内容一致时复用现有入口；有兼容性差异时才准备目标控制目录。
- 复用升级器已有的依赖哈希缓存，以回执中的 `venv_reused` 和依赖校验为准；依赖变化仍需安装，不手工替换缓存或为了提速跳过校验。安装器选择以部署用户环境为准，不把提权后找不到 uv 当作需要重新搭建安装流程。
- `update verify` 的部分健康信息来自 `upgrade_status` 历史记录。升级后仍独立检查 active symlink/版本、项目解释器的 `pip check`、当前服务健康、failed units 和 drift；不要把历史状态当实时验收。
- 已确认发布目标后，apply 预览和执行均显式传同一 `--target-version`；验收该目标时使用受支持的 `update verify --no-check-latest`，避免再次查询“最新版本”。仍核对实际 active 版本等于已发布目标；不凭 `ok` 接受别的版本，也不省略独立 live 服务验收。
- 一次只读验收可批量收集 active symlink/版本、`pip check`、`update verify --no-check-latest`、service drift、当前服务及 failed units。每项保留真实退出码和输出，缺项失败不能被最后一条成功掩盖；事实未变时不为总结再运行一轮。
- OM 本地 `--full` 与 PR/main 的必需 CI 分属不同证据，不因重复运行全量测试便直接删门禁。若测试使用 checkout 下 `.venv/bin/python`，开始 full 前核对该路径；仅设置外部 `OM_PYTHON` 不足以满足这些测试。
- 若实际入口支持 `--report-dir`，预检保存完整日志；update 保存原有 JSON，只精简终端成功命令输出。update 的子进程输出可能本来就有尾部长度限制，报告文件不能恢复已截断的内容。

## Portfolio Management (PM)

- 本机源码通常在 `/Volumes/liuxie的硬盘/workspace/portfolio-management`。发布/升级边界及检查命令见 `AGENTS.md`，安装细节见 `docs/deploy-linux.md`。
- 版本真源 `VERSION`，对应 `CHANGELOG.md` 和 `.github/workflows/release.yml`。按当前项目约定核实 tag 触发和产物要求，不复制其它项目的发布方式。
- 安装/升级入口为 `scripts/install.sh`，内部委托 `scripts/install_linux.py`。不带 `--apply` 也可能更新 checkout、创建 venv 并安装依赖，不能当纯只读预检。
- 普通 `--apply` 的安装成功不证明常驻服务已重启；`--enable-*` 又可能激活服务。按当前参数和项目规定分别执行授权的服务变更、preflight 和 API/监听服务健康验收，不擅自添加 enable 参数。
- 若当前脚本支持 `--report-dir`，使用其私有日志和紧凑安装结果；`scope=install` 只证明安装命令，`target_ref` 只是请求值。另行核验实际 checkout commit、活动服务与健康。

报告选项可能尚未合入或部署到目标版本；必须查当前源码或安全的 help 入口，不能根据本机实验工作区假设远端支持。其它项目直接从其 `AGENTS.md` 和原生入口建立本次映射；不默认使用 OM/PM 的路径或服务命令。
