# 代码与收口门槛

两个检查点复用现有流程，不增加人工审批：依赖现状的方案形成前检查code；整体确认/交接前检查ready。
纯方法讨论无需填写。没有保存授权时，记录留在会话草稿，使用stdin检查；不要为执行脚本擅自创建项目文件。

## 责任与通过条件

| 检查 | 必须提供的内容 | 阻塞条件 |
| --- | --- | --- |
| 代码现状 | 版本与未提交内容、入口到结果的链路、已有能力/缺口、相关配置/测试、未读边界 | 关键路径没读、版本漂移、依赖的事实缺证据；代码不可访问不算不适用 |
| 主流程 | 首个任务和已知不同场景的具体输入、步骤、可见结果、完成/退出 | 用户无法完成任务，关键行为仍需猜测 |
| 验收 | 每项核心结果的输入、判定、证明方法/环境、模拟边界、前置条件与负责人 | 验收无法证明承诺的结果，或把模拟结果当真实效果 |
| 跨时间 | 涉及持久状态时覆盖相关修改/取消/继续后的最终状态与禁止复活的旧结果 | 连续场景不闭合；无状态可说明不适用 |
| 判断依据 | 会改变产品方向的重要判断有对应证据或有理由不需研究 | 结论依赖的资料缺失；不强制每个需求做竞品调研 |

程序校验记录完整性、所读源码内容/HEAD及评审版本；内容评审判断代码引用是否支持结论、
主流程能否走通、验收是否足够、哪些场景应适用。程序不能证明agent真的阅读了代码，
不能检测全部遗漏调用链，也不能证明产品语义。不得把exit 0表述为自动语义验收。

主agent对当前完整PRD做反例评审并记录理由；仅有“已检查”不是内容评审。
复杂/高风险且有可用委派能力时可用独立只读reviewer，提供PRD、原始需求和代码证据，不提供预期结论。
没有独立reviewer可自审并注明，不能声称独立。实质缺口必须修复或回到产品决定，
仅因“不想阻塞”不能删除验收、将缺口写成不适用或标记pass。
技术实现细节/计划中的外部测试不是PRD必须现在完成的事项，但其行为和证明条件必须明确。

当前是Markdown skill加CLI检查器，没有宿主强制状态转换。调用方必须执行检查并消费非零退出；
未运行、记录缺失或结果不可用均不得宣称可交接。用户显式要求跳过时说明被跳过项目及限制，
可交付未核验草稿，不伪造通过记录。不要修改宿主配置或其他skill以假装获得不可绕过的门禁。

## 单一记录

PRD正文保留产品合同；一个`prdflow-gate` JSON代码块记录核查证据。检查项可引用正文的精确章节/验收ID，
不要复制第二份产品规则；引用是否成立由内容评审检查。
用户回复只报告需求结论、实际检查和缺口；已保存时链接文档，不默认展开JSON。无文件时
完整草稿与记录可保留在stdin校验调用中，最终答复无需重复它；交接必须能引用这份实际输入。
校验输出/进度说明属于正文之外的执行记录，不追加进已绑定指纹的PRD正文。正文验收与记录中的ID须完整对应，不能遗漏核心项。
`code.files`只列实际读过且支撑结论的文件，按需包括源码、配置和测试；`role`与`finding`解释作用和发现。
文件SHA256绑定包含未提交变动的实际字节；branch/revision记录当前检出，不冒充部署版本。
`comparison`写与已有参照分支的差异和未提交改动情况；未联网时如实声明，代码库没有Git时用`no-git`；已初始化但没有首次提交用`unborn`，仍核查实际骨架文件。
扫描结果不能代替实际打开相关代码。文件变化后先核对影响，再更新记录及评审，不直接重算hash宣称已重读。

下列仅是结构示例，不能作为实际检查证据；填入真实内容后才能使用。`code`采用下面两种之一。

```json
{
  "status": "pass",
  "reason": "相关链路已读，关键现状有代码依据",
  "root": "/absolute/project",
  "branch": "feature/example",
  "revision": "实际HEAD完整hash；无Git用no-git",
  "comparison": "已有参照分支/未提交差异及其影响，或无法比较的限制",
  "deployment": "部署版本证据或未核验",
  "chain": "入口文件:行号 → 处理 → 读写 → 返回/可见结果",
  "findings": "已有能力、可复用部分、真实缺口；数据承诺还应核实生产者保存信息",
  "limits": "未覆盖区域及对当前判断的影响；测试是已运行还是仅阅读",
  "files": [{"path": "src/entry.py", "sha256": "实际文件SHA256", "role": "入口", "finding": "行号和对现状判断的支持"}]
}
```

确实没有已有代码，或非软件需求：`{"status":"not-applicable","basis":"new-project或non-software","reason":"具体依据"}`。
已有仓库无法访问应记`status: blocked`并说明缺口，不能借N/A放行。新项目有骨架时仍核查骨架/依赖。

PRD附录记录形状：

````markdown
```prdflow-gate
{
  "schema": "prdflow-gate.v1",
  "code": {"status":"not-applicable","basis":"non-software","reason":"具体依据"},
  "walkthroughs": [{"scenario":"真实场景或正文位置","input":"具体输入","steps":["触发","操作与系统响应"],"result":"可见结果","exit":"完成或失败退出"}],
  "acceptance": [{"id":"A1","input":"输入/条件","criterion":"可观察通过条件或正文精确引用","method":"如何证明","environment":"所需环境","mock_boundary":"哪些可模拟，哪些必须真实；无则说明","prerequisites":"权限/数据等前置条件；无则说明","owner":"后续验收责任人或角色","evidence_status":"planned"}],
  "temporal": {"status":"not-applicable","reason":"无持久状态的具体依据"},
  "research": {"status":"not-applicable","reason":"不存在依赖外部资料的重要产品判断"},
  "blockers": [],
  "review": {"status":"pass","reviewer":"实际评审者","method":"self-review","rationale":"针对实际内容的检查结果/反例与裁决，可引用同文记录","content_sha256":"实际评审内容指纹"}
}
```
````

跨时间适用时：`temporal.status=pass`，增加`scenarios`列表，每项含`sequence`、`final_state`、`must_not_recur`。
研究适用时：`research.status=pass`，`reason`引用实际依据及取舍；缺依据用blocked。
验收`evidence_status`允许planned/verified/unverified/failed；verified/failed必须有`evidence`引用和实际结果。
planned/unverified不自动阻塞PRD；缺证明计划才阻塞。失败若证伪产品承诺，应记blocker并重新决策。
代码核查阶段可先只填写schema和code；ready阶段才要求其余项目。阻塞项保留在`blockers`，不能以评审pass覆盖。

## 执行

使用当前skill目录中的脚本，路径按安装位置解析。Python 3.9+，仅标准库，不修改任何文件或连接网络。

```sh
python3 /path/to/prdflow/scripts/check_gates.py /path/to/PRD.md --phase code
python3 /path/to/prdflow/scripts/check_gates.py /path/to/PRD.md --fingerprint
python3 /path/to/prdflow/scripts/check_gates.py /path/to/PRD.md --phase ready
```

`--fingerprint`只是生成待评审内容指纹，不是通过检查。内容评审覆盖正文和记录（排除review本身），
完成后填入`review.content_sha256`及真实裁决，再执行ready。正文或证据变化会使原评审失效。
无文件时用`-`从stdin读取同一份完整草稿；校验不可运行时保留未核验状态，披露阻塞，不新增安装权限。
记录实际退出结果；0表示该阶段结构/版本检查通过，1表示必须补齐或重新核对。接收方可执行相同命令复验。
