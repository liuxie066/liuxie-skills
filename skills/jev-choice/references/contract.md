# Jev 请求/响应契约核对表

本文件只记录**字段类型与边界**这类会改变实现决策的事实。完整概念、cookbook 与最新契约以 vendor 文档为准：<https://docs.typesafe.ai/llms.txt>。

## 端点

| 项 | 值 |
|---|---|
| 方法/URL | `POST https://api.typesafe.ai/v1/systemone`（**无尾斜杠**） |
| 认证 | `Authorization: Bearer <key>` |
| 请求体 | `{"model", "state", "questions"}` —— 恰好三个字段，无 `stream` / `temperature` / `max_tokens` |
| 默认模型 | `jev-latest`（响应里回显解析后的具体版本；本机实测为 `jev-1.13.0`，**不带厂商前缀**——第三方网关的文档示例会写成 `typesafe/jev-1.13-…`，那是网关的形状，不是本端点的） |
| 计费 | 按 input token；output 免费。$0.042 / M input tokens |
| 限流 | 250k tokens/s，1200 req/min；单请求约 32k token 上下文 |
| 延迟 | 厂商报告 70–500ms |

**尾斜杠会触发 307 并降级到 `http://`。** 本脚本显式拒绝一切 3xx，绝不跟随。

## 三种题型

| | `choice` | `score` | `noul` |
|---|---|---|---|
| `instructions` | 必填 | 必填 | 必填 |
| `criteria` | 必填**对象**：选项 key → 描述 | 必填**数组**，低→高，2–10 项 | 可选**对象** `{true, false}` |
| 上限 | 255 个选项 | 10 档 | — |
| 响应字段 | `choice`, `confidence`, `probabilities` | `score`, `confidence`, `legend`, `probabilities` | `noul` |
| 概率键 | 选项 key（与 criteria 同集） | **字符串档位下标** `"0"`…`"n-1"` | 无 |
| 有无 confidence | 有 | 有 | **无** |

### 容易记错的三处

1. **`score` 的 `legend` 是对象不是数组**：`{"0": "平静", "1": "不满"}`。它与 `probabilities` 同键集，而 `probabilities` 的键是**字符串下标**，不是 criteria 的文本。
2. **`noul` 只有两个字段**（`type`、`noul`）。它没有 `probabilities` 也没有 `confidence`，无从"套用 choice 的校验"。0.5 表示信息量为零。
3. **`score` 可以是小数**（如 1.34），表示概率加权后的期望档位；范围是 `0` 到 `len(criteria)-1`。

## 响应

```json
{"model": "typesafe/jev-1.13-20260917",
 "answers": {"<question key>": {"type": "...", ...}},
 "usage": {"input_tokens": 403, "output_tokens": 73}}
```

- `answers` 按**请求时的 key** 逐条返回。缺 key 视为致命错误。
- `usage` 的字段可以是 `None`，不得断言其存在或类型。
- 未知字段应被忽略并**原样透传**，不要重建 `answers`。

## 错误

| 状态 | kind | 含义 |
|---|---|---|
| — | `missing_key` | 本地没找到凭据，**未发出任何请求** |
| 401 | `authentication` | Key 无效 |
| 403 | `authentication` | 请求未带 `Authorization` 头 |
| 422 | `invalid_request` | 请求体不合法；`detail` 通常是一个**列表** |
| 429 | `rate_limited` | 尊重 `Retry-After` |
| 529 | `overloaded` | — |
| 503 | `overloaded` | **未见于文档**；从移植的客户端继承而来 |
| 3xx | `redirect` | 一律拒绝 |
| 其他 | `http` | 含 HTML 错误页（`detail` 会带 `content-type` 与前 200 字符） |

`detail` 的形状是 `str | dict | list` 三种都可能。

**鉴权早于请求体校验**：坏 Key + 合法 body 返回 401 而不是 422。所以没有可用 Key 时，只能靠 `--dry-run` 做请求形状检查。

## 校验分级

**致命**（契约保证或结构不变量，不满足即拒绝，绝不重试）：

- `answer.type` 与 `question.type` 一致；`answers` 覆盖全部请求 key
- `choice`：`choice` ∈ criteria；`set(probabilities) == set(criteria)`
- `score`：`set(probabilities) == {str(i) for i in range(len(criteria))}`；`set(legend) == set(probabilities)`；`0 <= score <= len(criteria)-1`
- `noul`：数值、有限、∈ [0,1]
- 每个概率**是数值且非 bool**、有限、∈ [0,1]；`confidence` 同

**建议级**（文档为真但对舍入敏感，进 `warnings`，`--strict` 才收紧）：

| 检查 | 默认容差 | `--strict` |
|---|---|---|
| 概率和 = 1 | `max(0.02, 0.005 × 键数)` | `0.02` |
| `choice` 是 argmax | `0.005` | `1e-6` |
| `score ≈ Σ i·pᵢ` | `0.05`，**仅警告** | 同 |
| `legend` 文本与 criteria 相符 | 仅当两者都是字符串时比 | 同 |

三处**不得"化简"**的写法：

- `type(x) in (int, float)` —— `bool` 是 `int` 子类，换成 `isinstance` 会静默接受 `true` 当概率。
- **先 `isfinite` 再比较** —— `nan < 0.8` 是 `False`，NaN 会**通过**置信度闸门。
- 响应解析用 `object_pairs_hook` 拒**重复键**；`parse_constant` 拒 `NaN`/`Infinity`。

## 置信度

厂商**没有**规定 confidence 的算法，由调用方自行定义，因此本工具**不做** confidence 与分布的一致性校验，也不实现任何具体公式（如第三方常见的 `1 − H(p)/ln K`）。`certainty` 仅作闸门用的统一标量：`choice`/`score` 取 `confidence`（`certainty_basis: "vendor"`），`noul` 取 `|noul − 0.5| × 2`（`certainty_basis: "derived_from_noul"`）。
