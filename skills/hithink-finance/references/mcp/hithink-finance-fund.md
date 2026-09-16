# hithink-finance-fund 工具契约

用于公募基金资料、公司、经理、披露数据、财务、净值、收益、公开资讯和场内基金行情。服务地址为 `https://fuyao.aicubes.cn/mcp/fund`。名称或代码未消歧时，先调用 `hithink-finance-meta` 获得带市场后缀的唯一 `thscode`。

## 工具

| 工具 | 适用场景 | 关键参数与边界 | 常见错误 |
| --- | --- | --- | --- |
| `get_fund_backtest_result` | 执行无状态基金在线回测 | `thscode`；`buy_conditions`/`sell_conditions` 为 JSON；频率、次数和金额必填 | 猜测指标规则，或把回测结果当收益承诺 |
| `get_fund_backtest_indicators` | 查询回测指标目录 | 无参数；读取指标编码、操作符与状态规则 | 固化未返回的指标或操作符 |
| `get_fund_indicators_line` | 查询画线式基金指标 | `indexes`/`time_range` 为 JSON；完整 `thscodes`；绝对时间为 Unix 毫秒 | 传秒值、裸代码或删除局部 null |
| `get_fund_indicators_table` | 查询表格式基金指标 | 四项 JSON 参数均可选；证券选择器用 `thscodes`；可返回 `part_order_thscodes` | 为可选参数注入默认值或混用 values/thscodes |
| `get_fund_quota_summary` | 查询 QDII 分类额度汇总 | `tab` 是 JSON 字符串数组 | 把 tab 当逗号分隔字符串 |
| `get_fund_quota_list` | 查询 QDII 基金额度列表 | `tab` 必填；`buy` 可选 boolean；`quota=null` 表示无限额 | 把 null 额度补零或当无数据 |
| `get_fund_profile_detail` | 查询基金基本资料 | 单个 `thscode` | 使用不完整代码，或把可空资料补写为确定值 |
| `get_fund_portfolio_holdings` | 查询定期披露重仓股 | 单个 `thscode`；`hold_ratio` 是百分数值 | 把披露持仓当实时组合，或把 8.88 解释为 0.0888% |
| `get_fund_performance_nav` | 查询最新或固定区间净值 | 单个 `thscode`；`range=week/month/tmonth/hyear/year/twoyear/tyear/fyear`；`nav_type=unit/adj/unit,adj`，默认二者 | 把 range 当自定义日期；忽略未选择字段会被省略 |
| `get_fund_performance_returns` | 查询固定区间收益 | 单个 `thscode`；返回月/季/半年/年/三年/五年/今年/成立以来 | 把固定区间字段当任意起止日期收益 |
| `get_fund_holders_detail` | 查询持有人结构 | 单个 `thscode`；`merge_scope=all/merged/separate`，默认 `all`；返回实际口径与报告日 | 把持有人结构当实时账户统计，或把 `all` 误当作实际记录口径 |
| `get_fund_market_snapshot` | 查询 ETF/LOF 场内快照 | 单个 `thscode` | 对场外基金或 REITs 重试 `3004` |
| `get_fund_market_historical` | 查询 ETF 前复权历史日线 | 单个 ETF；固定前复权；`interval=1d`；`start/end` 为毫秒戳；最多 5 年；无 `adjust` | 传 LOF、复权参数、批量代码或超过 5 年窗口 |
| `get_fund_companies_detail` | 查询基金公司详情 | `company_id` 必填 | 用基金代码代替公司 ID |
| `get_fund_portfolio_industry_allocation` | 查询基金行业配置 | 单个 `thscode` | 把定期披露占比当实时配置 |
| `get_fund_performance_indicators_historical` | 查询基金净值波动、趋势强弱与估值百分位序列 | `thscode`、`start`/`end` 均必填，区间最多 5 年；固定周期 `DAY_1`，data 仅含 timestamp/item，不返回顶层 thscode/interval | 只传一个边界、查询超长窗口或把用户侧含义作为参数或字段名传入 |
| `get_fund_performance_drawdowns` | 查询主要回撤区间 | 单个 `thscode` | 把历史回撤解释为未来风险承诺 |
| `get_fund_holders_top` | 查询前十大持有人 | 单个 `thscode`；`limit` 可选且不超过 10 | 请求完整账户明细 |
| `get_fund_corporate_actions_dividends` | 查询基金分红记录 | 单个 `thscode` | 把累计分红当总收益 |
| `get_fund_diagnostics_detail` | 查询基金诊断详情 | 单个 `thscode`；含 `radar_comparison` | 将诊断字段改写为买卖建议 |
| `get_fund_financials_indicators` | 查询基金财务指标 | 单个 `thscode` | 与 A 股财务指标混用 |
| `get_fund_financials_income_statements` | 查询基金利润表 | 单个 `thscode` | 期待公司主营业务字段 |
| `get_fund_financials_balance_sheets` | 查询基金资产负债表 | 单个 `thscode` | 把可空披露值补零 |
| `get_fund_managers_investment_style` | 查询基金经理投资风格 | `manager_id` 必填 | 用基金代码代替经理 ID |
| `get_fund_managers_performance` | 查询基金经理区间业绩 | `manager_id`；`range=month/tmonth/year/nowyear/now` | 把 range 当自定义日期 |
| `get_fund_managers_experience` | 查询基金经理任职经历 | `manager_id` 必填 | 把历史任职产品当当前在管 |
| `get_fund_managers_detail` | 查询基金经理详情 | `manager_id` 必填 | 根据姓名猜测不唯一的 ID |
| `get_fund_news_article_list` | 查询基金公开资讯元数据列表 | 单个 `thscode`；`limit=1..100`；`offset` 是不透明游标；不返回 total，按 `has_more=false` 结束分页 | 期待正文、读取不存在的总数或自行拼接游标 |
| `get_fund_offerings_list` | 查询在售或待售基金 | `subscribe=active/upcoming` | 把发行状态当可直接交易 |
| `get_fund_portfolio_stock_history` | 查询指定报告期股票持仓 | 单个 `thscode`；`report_type` 与 `end_date` 必填；`rank` 仅前十为 `1`～`10`，其余为 `null` | 把历史披露当实时持仓，或用 `rank` 过滤完整持仓 |
| `get_fund_portfolio_stock_report_dates` | 查询股票持仓可用报告期 | 单个 `thscode`；`report_type` 可选 | 猜测不存在的报告期 |
| `get_fund_portfolio_bond_history` | 查询指定报告期债券持仓 | 单个 `thscode`；`report_type` 与 `end_date` 必填；`rank` 仅前十为 `1`～`10`，其余为 `null` | 与股票持仓字段混用，或用 `rank` 过滤完整持仓 |
| `get_fund_portfolio_bond_report_dates` | 查询债券持仓可用报告期 | 单个 `thscode`；`report_type` 可选 | 猜测不存在的报告期 |
| `get_fund_portfolio_asset_allocation` | 查询大类资产配置 | 单个 `thscode` | 把定期披露占比当实时仓位 |

## 参数与错误语义

- 按基金查询的工具使用带市场后缀的单个 `thscode` 唯一定位基金。
- 六项基金功能工具的复杂对象和数组参数都是 JSON 字符串；画线和表格绝对时间使用 Unix 毫秒，0/负值保留位置语义。
- 六项工具保留动态业务键、数值字符串和局部 `null`；响应不缓存、不保存回测任务。
- `get_fund_performance_indicators_historical` 返回字段含义为：`rsi_pct`：净值波动（RSI）；`donchian_channel`：趋势强弱（唐奇安通道）；`track_index_pe_ttm_five_year_percentile`：估值百分位（跟踪指数 PE TTM 五年分位）。调用后仍从这三个原有 JSON 字段读取数据。
- `get_fund_holders_detail` 的 `merge_scope=all` 最多返回 `merged`、`separate` 各一条最新披露记录；每条记录的 `merge_scope` 是实际口径，`report_date_ms` 是该条报告日，顶层 `timestamp` 取返回记录中的最新报告日（均为毫秒戳）。
- `market/snapshot` 支持 ETF 与 LOF，`market/historical` 当前只支持 ETF。
- `3001` 表示基金未找到；回到 meta 搜索核对 `asset_type` 和 `thscode`。
- `3002` 表示数据尚未准备；保留 `request_id`，不要补零或使用模拟数据。
- `3004` 表示目标基金类型不支持该能力；改选适用工具，不重试原参数。

## Agent 选型

1. 名称、纯 ticker 或不确定代码先用 `get_meta_tickers_search`；可用 `asset_type=fund-otc,fund-etf,fund-lof,fund-reits` 缩小范围。
2. 用户问资料、经理、披露、财务、净值、收益、诊断、持有人或公开资讯时，根据搜索结果或已知 ID 选择对应工具。
3. 用户问交易所价格时，ETF/LOF 用 snapshot；只有 ETF 能用 historical。
4. 长结果或多基金循环必须落盘，只摘要路径、数量、窗口和口径。

## 边界

- 不提供基金申购、赎回、交易执行、基金推荐或收益承诺；资讯工具只返回公开文章元数据列表。
- 工具契约不等于当前会话已连接；首次调用或参数错误后读取该服务的 `tools/list`。
