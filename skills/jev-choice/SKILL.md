---
name: jev-choice
description: "把 TypeSafe Jev 决策 API 当作可复用的本地判断客户端：一次请求提交多个 choice / score / noul 问题，拿回结构化答案、概率与置信度，并在本地按请求校验响应后再交给调用方。当用户提到 Jev、TypeSafe、System One，或要求对文本、工单、记录、候选项做分类、路由、多档打分、二值判断、阈值判定时使用；需要完整排序或名次、事实检索、计数或算术、日期比较、文本生成，或要把结果当安全控制与执行授权时不适用。"
---

# Jev Choice

把 TypeSafe 的 Jev 当成本地可调用的判断客户端：一次请求提交多个 typed 问题，拿回结构化答案、概率与置信度，**在本地按请求校验过**才交给调用方。

**这是可执行客户端，不是文档导航。** 需要 API 设计指导、题型选择、cookbook 或最新契约时，以 TypeSafe 官方的 `typesafe-ai` skill 与 <https://docs.typesafe.ai/llms.txt> 为准。本 skill 负责真正发请求、校验响应、管凭据、分错误——选它是因为要**做出一次判断**，不是为了查文档。

**前置：需要一个可用的 TypeSafe key（见「凭据」）。** 没有它，脚本只会返回 `missing_key`，**拿不到任何判断**——`--dry-run` 仅能验证请求形状，不能替代答案。所以：起草 spec 之前先确认凭据可用；用户在本次任务里明确禁止接触凭据时，不要为此去搜索或配置，直接把 `missing_key` 报告出去。

## 何时使用

答案的**取值范围事先已知**时：分类、路由分派、候选项排序、按维度打分、二值判断、阈值判定、从已知选项里挑一个最合适的。典型形状是"从这 N 个里选一个"或"这件事有多严重"。

多个问题**合成一次请求**：它们并行作答，只多花 token，不额外增加往返延迟。

## 何时不使用

计数与算术、日期运算与时间窗口比较、事实检索、多跳推理、文本生成/摘要/翻译——这些用代码或推理模型。也不要把结果当安全控制、权限判定或内容过滤器，不要用来授权高影响且不可逆的动作。详情见文末「边界」。

## 凭据

按序查找，命中即用：

1. 环境变量 `TYPESAFE_API_KEY`
2. 用户级凭据文件（`TYPESAFE_API_KEY=<key>` 单行，不加引号，权限 0600）：
   - macOS `~/Library/Application Support/typesafe/credentials.env`
   - Linux `${XDG_CONFIG_HOME:-~/.config}/typesafe/credentials.env`
   - Windows `%APPDATA%\typesafe\credentials.env`

**不要主动去搜凭据。** 直接跑脚本即可：它会自己按上面的顺序解析，输出里的 `credential_source` 就是本次用的来源；`missing_key` 就是"没找到"的确切答案。遍历环境变量与各路径去找 Key，既没有额外信息，又容易在用户已经限定了凭据操作的任务里撞上权限拦截。

任何情况下都只报告凭据的**来源与存在状态，绝不显示值**。不要要求用户把 Key 发到对话里；不要把它写进命令参数、脚本、产物、日志或任何仓库文件。

在 Claude Code 里，把 Key 放进 `~/.claude/settings.json` 的 `env` 块即可：插件类消费者会直接读该文件，而本脚本依赖 harness 把它注入进程环境——**这一点在配置后需实测确认**，因为脚本本身不读 `settings.json`。

## 调用方式

**先把 spec 写成文件，再用 `--spec` 读它。** criteria 和 instructions 是自然语言，常含撇号、引号、`$`；走 shell 内联 JSON 必然踩引号转义。用 Write 工具落盘是零风险路径。

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-$HOME/.agents/skills/jev-choice}"
python3 "$SKILL_DIR/scripts/jev_choose.py" --spec /tmp/jev_spec.json
```

`--spec -` 读 stdin，是给程序化调用用的；手写场景不要用 heredoc。

spec 就是 vendor 的请求体本身，不做任何包装：

```json
{
  "model": "jev-latest",
  "state": "客服工单全文，或一个结构化对象",
  "questions": {
    "team": {
      "type": "choice",
      "instructions": "这个工单该由哪个团队受理？",
      "criteria": {
        "billing": "付款、发票、退款",
        "technical": "缺陷、故障、集成"
      }
    },
    "frustration": {
      "type": "score",
      "instructions": "客户有多不满？",
      "criteria": ["平静", "不满", "非常愤怒"]
    },
    "urgent": {
      "type": "noul",
      "instructions": "这个工单表达了紧迫性吗？"
    }
  }
}
```

**spec 不平凡时先 `--dry-run`。** 它跑完整的本地请求校验、打印将发送的 body、且**不出网**——这是唯一免费的形状检查（在线时鉴权早于 422，坏 Key 会直接返回 401，看不出请求本身有没有问题）。

## 请求契约

| 类型 | 必填 | 判据形状 | 限制 |
|---|---|---|---|
| `choice` | `instructions` + `criteria` | 对象：选项 key → 描述 | ≤255 个选项 |
| `score` | `instructions` + `criteria` | **数组**，低到高排列 | 2–10 档 |
| `noul` | `instructions` | 可选对象 `{true, false}` 描述含义 | 无分布、无 confidence |

- `instructions` 可以是字符串、对象或数组；结构化指令用对象/数组更清楚。
- `state` 是字符串、对象或数组，**仅文本**。
- 一次请求的 `state` + `questions` 共享约 32k token 预算。超过 `--max-state-bytes`（默认 120000 字节）会警告——该裁的是**与本次判断无关的 state**，因为无关上下文会拉低准确率，不是会被硬拒。
- 问题 key 只给代码用，不会送给模型；把完整含义写进 `instructions` 和 `criteria`。

**多条目批次**（N 个工单/记录走同一套问题）时，把**共享材料**放 `state`，把**单条特有的内容**放进该条自己的 `instructions`——不要把所有条目都堆进 `state` 再问逐条问题。后者会让每个判断都看到 N−1 条无关材料，而无关上下文正是会拉低准确率的东西。这里有个真实取舍：一次请求装下全部 N 条最省 token，但 state 越大越容易触达上面的告警线；准确率优先于费用时就拆成多次请求，并把这是有意为之讲清楚。

## 输出契约

```json
{"ok": true, "dry_run": false,
 "model_requested": "jev-latest", "model": "jev-1.13.0",
 "answers": { "...API 原样返回，未重建..." },
 "validation": {"team": {"type": "choice", "certainty": 0.97,
                          "certainty_basis": "vendor",
                          "top_probability": 0.98, "warnings": []}},
 "usage": {"input_tokens": 403, "output_tokens": 73},
 "latency_ms": 231, "attempts": 1, "request_id": "req_…",
 "credential_source": "environment (TYPESAFE_API_KEY)",
 "state_sha256": "…", "state_bytes": 812, "warnings": []}
```

**`ok` 是唯一判据。** 退出码只区分工具错误（`1`）与参数用法错误（`2`），不代表判断质量。

- `model_requested` 与 `model` 是**两个不同的值**：前者是你请求的 `jev-latest`，后者是服务端解析出的具体版本。记录决策时要留下 `model` ——同一个判断在不同解析版本下不可复现。
- `answers` 原样透传，不重建，以免隐藏新增字段。
- `validation.<key>.warnings` 是**建议级**观察（概率和漂移、非 argmax、legend 文本不符），不影响 `ok`。`--strict` 会把容差收紧到移植时的原值。
- `noul` 没有 confidence。工具为它派生的 `certainty` 标了 `certainty_basis: "derived_from_noul"`——引用时要说清这是派生的，不是厂商返回值。
- `--min-confidence` 未达标**不改变退出码**，只在 `below_threshold` 里列出问题名并把 `gate.passed` 置 false。需要非零码的调用方显式加 `--fail-below-threshold`。

## 解读结果

- **`confidence` 不是"选对的概率"。** 它只概括概率分布的集中程度，与判断是否正确、是否获得执行授权无关。候选数量不同时不可直接比较。**不要用最高概率代替 confidence，也不要反过来**——`top_probability` 0.98 与 `confidence` 0.86 同时出现是正常的。
- **概率不是正确率。** 类型化输出保证的是接口，不是事实。Jev 在你的领域是否校准，必须在你的数据上自行验证；不要把 cookbook 里的阈值当通用规则。
- Jev 不能计数、不能做算术、不能把日期当有序量比较。`score` 的数值校准较弱——**把它当有序档位，不要当精确测量**，不要对 score 再做阈值算术。
- 一个命题和它的否定不必加起来等于 1；`noul` 与 `choice` 的数字不可直接比较，阈值不可跨题型搬运。
- `noul` 的 0.5 表示信息量为零，不是"中等强度"。
- 重复提交同一个 `state` + `questions` **不构成独立证据**。需要稳定性时显式多次采样、在代码里聚合，并说明这是有意的。
- state 含第三方内容时，答案可能被其中内容影响。此类结果**不能作为安全控制或权限判断的唯一依据**。
- 低置信应路由到人工复核或改用推理模型；高风险、不可逆的动作仍需用户确认。**本工具只提供判断，不授权执行。**

## 错误处理

| kind | 含义 | 该做什么 |
|---|---|---|
| `missing_key` | 没找到凭据，**什么都没发送** | 按「凭据」一节配置，不要重试 |
| `authentication` | 401/403，凭据被拒 | 修凭据，不要重试 |
| `invalid_request` | spec 本地校验失败，或服务端 422 | 修 spec；422 的 `detail` 就是全部价值，原样读 |
| `validation` | 响应未通过致命校验 | **不要重试、不要放宽**。这是 fail-closed 生效了 |
| `invalid_response` | 响应非 JSON、含重复键或 NaN、缺 `answers` | 视为服务端异常，可报告 `request_id` |
| `rate_limited` / `overloaded` | 429 / 529 | 唯一可重试的情形，且工具已按 `Retry-After` 退避过 |
| `redirect` | 3xx，被显式拒绝 | 不要绕过——该端点的重定向会降级到明文 HTTP |
| `tls` | 证书校验失败 | 该 Python 没有可用 CA bundle，重装或设 `SSL_CERT_FILE` |
| `network` / `http` | 连接失败、超时、其他状态码 | 看 `status` 与 `detail` 再定 |

## 边界

不适用：计数与算术（用代码）；日期运算与时间窗口比较（先抽取，再用代码比较）；事实检索、需要外部证据或最新事实的问题（先检索）；多跳推理与长链条推导（用推理模型）；文本生成、摘要、翻译（用生成式模型）；把 Jev 当安全控制、权限判定或内容过滤器；高影响且不可逆的自动决策（需用户确认）；以及任何要求代持密钥或把凭据写入仓库文件的场景。

费用：Jev 按 input token 计费。把问题合成一次请求；不要为试探而发散调用；把 `usage` 报给用户。

字段类型、限制与错误码的完整核对表见 [references/contract.md](references/contract.md)。
