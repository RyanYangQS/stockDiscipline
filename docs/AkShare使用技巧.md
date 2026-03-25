# 量化入门第1篇：用AKShare抓股票数据，新手也能秒上手
作者：极客笔记Jack
发布时间：2025-12-05

【导语】股票量化新手常被“找数据”难住？手动导Excel、啃复杂接口太耗时。推荐量化神器AKShare：纯免费、零门槛，一行代码拉取A股日K、财务等核心数据，新手速学速用。

## 一、为什么入门量化先学AKShare？
AKShare对新手友好度拉满，三大核心优势：
- **免费无门槛**：无需注册积分，安装即调用，省却工具准备时间。
- **股票数据全覆盖**：日K、财务、龙虎榜、股东持仓等量化所需数据一站获取。
- **极简易用**：API命名直观，如`stock_zh_a_daily`即取日K数据，无需死记参数。

提醒：AKShare数据来自公开渠道，非商用合规；实盘决策需结合官方数据源交叉验证。

## 二、3分钟搞定：AKShare环境搭建
电脑装Python后，两步完成配置，命令直接复制：

### 1. 安装AKShare库
Windows开cmd、Mac开终端，执行：
```bash
pip install akshare --upgrade  # 安装并更新到最新版
```

### 2. 安装辅助工具
配装数据处理库pandas和Excel保存库openpyxl：
```bash
pip install pandas openpyxl
```
完成后打开PyCharm社区版（免费），即可开始编码。

## 三、核心实操：5个股票高频场景，代码直接抄
精选日K、财务等5大高频场景，代码附详细注释，改股票代码即可用。

### 场景1：获取A股日K数据（核心需求）
以宁德时代（300750）为例，获取2024年1-10月前复权日K数据：
```python
import akshare as ak
import pandas as pd

# 调用日K接口，qfq前复权适配实盘分析
stock_df = ak.stock_zh_a_daily(
    symbol="300750", start_date="2024-01-01", end_date="2024-10-31", adjust="qfq"
)

stock_df = stock_df.reset_index()  # 日期从索引转普通列
stock_df["涨跌幅"] = stock_df["close"].pct_change() * 100  # 计算涨跌幅

# 保存到桌面，路径按自身电脑修改
stock_df.to_excel("C:/Users/Admin/Desktop/宁德时代日K2024.xlsx", index=False)
print("宁德时代日K核心数据（前5行）：")
print(stock_df[["date", "open", "close", "volume", "涨跌幅"]].head())
```

### 场景2：获取上市公司财务数据（价值量化）
以贵州茅台（600519）为例，提取2023年核心财务指标：
```python
import akshare as ak

# 获取核心财务数据，筛选2023年有效数据
finance_df = ak.stock_financial_analysis_indicator(symbol="600519", indicator="financial_indicator")
finance_2023 = finance_df[
    finance_df["报告期"].str.contains("2023") & finance_df["净利润(亿元)"].notna()
]

# 提取ROE、毛利率等价值投资指标
key_indicators = finance_2023[["报告期", "净利润(亿元)", "净资产收益率(%)", "毛利率(%)"]]
print("贵州茅台2023年核心财务指标：")
print(key_indicators.round(2))
```

### 场景3：获取龙虎榜数据（捕捉主力）
筛选2024-10-30机构净买入超1000万的股票：
```python
import akshare as ak

# 调用龙虎榜接口，计算机构净买入
longhu_df = ak.stock_zh_a_lhb_detail(trade_date="2024-10-30", market_type="stock_zh_a")
longhu_df["机构净买入"] = longhu_df["机构买入额"] - longhu_df["机构卖出额"]

# 筛选机构净买入超1000万标的并排序
institution_buy = longhu_df[longhu_df["机构净买入"] > 10000000]
key_longhu = institution_buy[["股票代码", "股票名称", "机构净买入"]].sort_values("机构净买入", ascending=False)

print("2024-10-30 机构净买入超1000万股票：")
print(key_longhu.head())
```

### 场景4：获取分时数据（日内交易）
以比亚迪（002594）为例，获取2024-10-31 1分钟分时数据：
```python
import akshare as ak
import pandas as pd

# 调用1分钟分时接口，筛选有效交易时间
time_share_df = ak.stock_zh_a_minute(symbol="002594", trade_date="2024-10-31", frequency="1")
time_share_df["时间"] = pd.to_datetime(time_share_df["时间"])
trade_time_df = time_share_df[
    ((time_share_df["时间"].dt.hour == 9) & (time_share_df["时间"].dt.minute >= 30)) |
    ((time_share_df["时间"].dt.hour.between(10, 11)) & (time_share_df["时间"].dt.minute <= 30)) |
    (time_share_df["时间"].dt.hour.between(13, 15))
]

print("比亚迪2024-10-31 分时数据（前10行）：")
print(trade_time_df[["时间", "收盘", "成交量"]].head())
```

### 场景5：获取股东持仓数据（长期投资）
以紫金矿业（601899）为例，提取2023年年报机构股东数据：
```python
import akshare as ak

# 调用股东结构接口，筛选机构股东
holder_df = ak.stock_zh_a_shareholder_structure(symbol="601899", report_type=1)  # 1=年报
institution_holder = holder_df[holder_df["股东类型"].str.contains("机构", na=False)]

print("紫金矿业2023年报 机构股东持仓（前10）：")
print(institution_holder[["股东名称", "持股数量(万股)", "持股比例(%)"]].head())
```

## 四、避坑技巧：AKShare使用4要点
1. **复权选前复权**：回测用qfq（前复权）匹配实盘成本，看历史高价用hfq（后复权）。
2. **代码用纯6位数字**：A股接口仅识别6位代码（如600036），带.SH/.SZ会报错。
3. **分时数据用交易日**：非交易日查询为空，可先用`ak.stock_zh_a_trade_date_hist_sina()`查交易日历。
4. **财务数据交叉验证**：明确指标定义（如归属母公司净利润），重要决策结合年报原文。
