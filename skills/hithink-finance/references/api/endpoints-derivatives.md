# 期货与期权端点

本页维护 13 个公开期货 REST 能力和 4 个公开期权 REST 能力。接口统一使用 `GET`、`X-api-key` 与 `{code,message,request_id,data}` 信封；端内专用能力不属于本页公开契约。

## 端点与参数

| operationId | 路径 | 参数 |
| --- | --- | --- |
| `get_futures_varieties_list` | `GET /api/futures/varieties/list` | 无 |
| `get_futures_contracts_detail` | `GET /api/futures/contracts/detail` | `thscode` 必填 |
| `get_futures_positions_variety_daily` | `GET /api/futures/positions/variety-daily` | `date` 必填，`YYYY-MM-DD` |
| `get_futures_positions_company_variety_daily` | `GET /api/futures/positions/company-variety-daily` | `date`、`varieties` 必填；`varieties` 为 1～5 个逗号分隔品种代码 |
| `get_futures_positions_contract_daily` | `GET /api/futures/positions/contract-daily` | `thscode`、`variety`、`date` 必填 |
| `get_futures_positions_contract_historical` | `GET /api/futures/positions/contract-historical` | `thscode`、`variety`、`company`、`start_date` 必填；开始日须在调用日前一年内 |
| `get_futures_positions_company_list` | `GET /api/futures/positions/company-list` | 无 |
| `get_futures_warehouse_receipts_historical` | `GET /api/futures/warehouse-receipts/historical` | `thscode`、`start_date`、`end_date` 必填 |
| `get_futures_basis_main_continuous_latest` | `GET /api/futures/basis/main-continuous-latest` | 无 |
| `get_futures_basis_historical` | `GET /api/futures/basis/historical` | `thscode` 必填，`spot_indicator_id` 可选 |
| `get_futures_calendar_trading_schedule` | `GET /api/futures/calendar/trading-schedule` | `thscode`、`start_date`、`end_date` 必填 |
| `get_futures_prices_intraday` | `GET /api/futures/prices/intraday` | `thscode` 必填；`session` 可取 `pre_market`、`intraday`、`post_market`，默认 `intraday` |
| `get_futures_prices_daily` | `GET /api/futures/prices/daily` | `thscode` 必填；`start`、`end` 为可选的成对正 Unix 毫秒 |
| `get_options_varieties_list` | `GET /api/options/varieties/list` | 无 |
| `get_options_contracts_detail` | `GET /api/options/contracts/detail` | `thscode` 必填 |
| `get_options_prices_intraday` | `GET /api/options/prices/intraday` | 与期货分时参数相同 |
| `get_options_prices_daily` | `GET /api/options/prices/daily` | 与期货日 K 参数相同，周期固定 `1d` |

`thscode` 必须是目录中目标资产域的完整代码。持仓查询的 `variety` 使用大写品种代码，并须与合约目录一致。日期起点不得晚于终点；日 K 省略 `start/end` 时返回最近 100 根。

```bash
curl -sS 'https://fuyao.aicubes.cn/api/futures/contracts/detail?thscode=RB2610.SHF' \
  -H 'X-api-key: YOUR_API_KEY'

curl -sS 'https://fuyao.aicubes.cn/api/options/prices/daily?thscode=MO2610-C-6500.CFX' \
  -H 'X-api-key: YOUR_API_KEY'
```

## 响应字段

- 品种资料：`variety_code,quote_code,name,exchange_code,exchange_name,has_night_session,margin_rate,main_contract_thscode,trade_amount,price_coefficient,price_unit,trade_unit,tick_size,contract_multiplier,capital_flow,long_short_ratio,transaction_fee,transaction_fee_rate,trade_sessions[]`。期权品种另含 `exercise_fee,settlement_type`。
- 合约详情：`timestamp,thscode,ticker,name,variety_code,variety_name,exchange_code,list_date,end_date,last_trade_date,last_delivery_date`。期权另含 `display_code,pinyin,margin_rate,underlying_code,strike_price,exercise_style,option_type,trade_amount`。
- 持仓：品种和公司品种结果含成交、持仓及变化、净持仓、均价、盈亏、情绪和资金字段。公司品种持仓中的 `price_spread_contract` 为可空字符串，值是逗号分隔合约文本。合约日持仓包装固定为 `timestamp,date,position_item[],average_item[]`；合约历史持仓包装固定为 `timestamp,start_date,end_date,position_item[],average_item[]`。两个数组含义独立，不得按数组位置关联。
- 仓单：`date,amount,amount_change,equivalent_lots`。
- 基差：最新结果含合约、现货来源、价格、结算价、基差、基差率、`average_close_basis` 和 `average_settle_basis`；`spot_publish_date` 非空时统一为 `YYYY-MM-DD`。历史点含 `date,spot_price,converted_spot_price,close_price,settle_price,close_basis,settle_basis,close_basis_rate,settle_basis_rate`。
- 日程：`trade_dates[]`,`regular_schedules[]`,`special_schedules[]`,`timezone`,`daylight_saving_periods[]`。
- 分时点：`timestamp,price,volume,turnover`；日 K：`timestamp,open_price,high_price,low_price,close_price,volume,turnover`。

列表与点位数组始终存在，合法无数据返回 `[]`。直接数组型 `data` 为 `null` 时归一为 `[]`；对象型 `data` 的必需数组容器缺失、为 `null` 或类型错误时返回 `5003`，只有显式 `[]` 表示合法空结果。价格、金额、数量、比例、日期、费用和名称均可能为 `null`（nullable）；不得补零或删除空值。品种持仓和公司品种持仓的 `date`、历史基差的 `date` 及 `spot_publish_date` 非空时统一为 `YYYY-MM-DD`，非法上游日期返回 `5003`。期权枚举 `option_type=call/put`、`exercise_style=bermudan/american/european`、`settlement_type=physical/cash`，未知编码保留原值。

## 错误

除通用错误外，`3001` 表示标的不存在，`3002` 表示衍生品目录未就绪，`3004` 表示标的不属于目标资产域；`5002` 表示上游超时，`5003` 表示上游拒绝、传输失败或响应无法解析。业务错误仍为 HTTP 200，`data=null`。

## 避错要点

- 先通过品种目录或标的搜索确认完整 `thscode`，不要根据简称自行拼接交易所后缀。
- `date/start_date/end_date` 使用 `YYYY-MM-DD`，日 K 的 `start/end` 使用 Unix 毫秒；不要混用两种时间格式。
- `session` 只表示盘前、盘中或盘后会话，不是 K 线周期；日 K 周期固定为 `1d`。
- 数值和日期字段允许为 `null`，合法空列表为 `[]`；不要把两者改写为零或缺失字段。
