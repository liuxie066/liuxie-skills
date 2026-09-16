# 期货 MCP 工具

适用场景：公开期货品种、合约、持仓、仓单、基差、交易日程和行情查询。参数与空值语义以 [REST 契约](../api/endpoints-derivatives.md) 为准。

| 工具 | 用途与参数 |
| --- | --- |
| `get_futures_varieties_list` | 查询期货品种；无参数 |
| `get_futures_contracts_detail` | 合约详情；参数 `thscode` |
| `get_futures_positions_variety_daily` | 品种日持仓；参数 `date` |
| `get_futures_positions_company_variety_daily` | 公司品种日持仓；参数 `date,varieties` |
| `get_futures_positions_contract_daily` | 合约日持仓；参数 `thscode,variety,date` |
| `get_futures_positions_contract_historical` | 合约历史持仓；参数 `thscode,variety,company,start_date` |
| `get_futures_positions_company_list` | 期货公司列表；无参数 |
| `get_futures_warehouse_receipts_historical` | 历史仓单；参数 `thscode,start_date,end_date` |
| `get_futures_basis_main_continuous_latest` | 主连最新基差；无参数 |
| `get_futures_basis_historical` | 历史基差；参数 `thscode,spot_indicator_id?` |
| `get_futures_calendar_trading_schedule` | 交易日程；参数 `thscode,start_date,end_date` |
| `get_futures_prices_intraday` | 当前分时；参数 `thscode,session?`，`pre_market/intraday/post_market` |
| `get_futures_prices_daily` | 固定 `1d` 日 K；参数 `thscode,start?,end?` |

`start/end` 必须成对提供；数组合法无数据时为 `[]`，金融数值允许 `null`。公司品种持仓的 `price_spread_contract` 是可空字符串；`spot_publish_date` 及持仓的 `date` 非空时为 `YYYY-MM-DD`。对象响应的必需数组容器缺失、为 `null` 或类型错误时返回 `5003`。大结果应落盘。
