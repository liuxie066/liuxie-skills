# 期权 MCP 工具

适用场景：公开期权品种、合约详情和行情查询。参数与空值语义以 [REST 契约](../api/endpoints-derivatives.md) 为准。

| 工具 | 用途与参数 |
| --- | --- |
| `get_options_varieties_list` | 查询期权品种；无参数 |
| `get_options_contracts_detail` | 合约详情；参数 `thscode` |
| `get_options_prices_intraday` | 当前分时；参数 `thscode,session?` |
| `get_options_prices_daily` | 固定 `1d` 日 K；参数 `thscode,start?,end?` |

`session` 可取 `pre_market/intraday/post_market`；`start/end` 必须成对提供。数组合法无数据时为 `[]`，金融数值允许 `null`。
