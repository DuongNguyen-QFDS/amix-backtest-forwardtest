import os
import numpy as np
import pandas as pd
from strategy import SYMBOLS, PARAMS, generate_weights

def _calc_full_metrics(dates, returns, rf_rate=0.05):
    dates = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    returns = pd.Series(returns).fillna(0).reset_index(drop=True)
    equity = (1 + returns).cumprod()

    years = len(returns) / 252.0
    cagr = (equity.iloc[-1] ** (1 / years) - 1) * 100 if years > 0 else 0.0
    ann_avg_ret = (returns.mean() * 252) * 100
    ann_vol = (returns.std() * np.sqrt(252)) * 100
    sharpe = ((returns.mean() * 252) - rf_rate) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0.0

    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_dd = abs(drawdown.min()) * 100

    max_dd_duration, peak_idx = 0, 0
    for i in range(len(equity)):
        if equity.iloc[i] >= rolling_max.iloc[i]:
            max_dd_duration = max(max_dd_duration, i - peak_idx)
            peak_idx = i
        elif i == len(equity) - 1:
            max_dd_duration = max(max_dd_duration, i - peak_idx)
            
    return {
        "From date": dates.iloc[0].strftime("%m/%d/%Y"),
        "To date": dates.iloc[-1].strftime("%m/%d/%Y"),
        "Compound annual growth rate (CAGR)": f"{cagr:.2f}%",
        "Annualized average returns": f"{ann_avg_ret:.2f}%",
        "Annualized volatility": f"{ann_vol:.2f}%",
        "Sharpe ratio": f"{sharpe:.2f}",
        "Max drawdown": f"{max_dd:.2f}%",
        "Max drawdown duration": f"{max_dd_duration} days",
        "Skewness": f"{returns.skew():.2f}",
        "Kurtosis": f"{returns.kurt():.2f}",
        "Value at risk (VAR 95%)": f"{np.percentile(returns, 5) * 100:.2f}%"
    }

def run_backtest(oos_ratio=0.3):
    data_dict = {sym: pd.read_csv(f"data/{sym}_raw.csv") for sym in SYMBOLS if os.path.exists(f"data/{sym}_raw.csv")}
    if not data_dict:
        print("[Lỗi] Chưa có dữ liệu. Hãy chạy bước 1 trước.")
        return

    weights_df = generate_weights(data_dict)

    # Lọc theo khoảng thời gian cấu hình trong strategy.py
    start_date = PARAMS.get("start_date")
    end_date = PARAMS.get("end_date")
    if start_date or end_date:
        weights_oos = weights_df.loc[start_date:end_date]
    else:
        split_idx = int(len(weights_df) * (1 - oos_ratio))
        weights_oos = weights_df.iloc[split_idx:]

    held_weights = weights_oos.shift(1).fillna(0)
    turnover = held_weights.diff().abs().fillna(0)

    returns_df = pd.DataFrame({
        sym: df.assign(date=pd.to_datetime(df['date']))
               .sort_values('date')
               .drop_duplicates('date')
               .set_index('date')['close']
               .pct_change()
        for sym, df in data_dict.items()
    }).reindex(weights_oos.index).fillna(0)

    rf_rate, fee_rate = PARAMS.get("rf_rate", 0.05), PARAMS.get("fee_rate", 0.0015)
    all_metrics = {
        sym: _calc_full_metrics(weights_oos.index, (held_weights[sym] * returns_df[sym]) - (turnover[sym] * fee_rate), rf_rate)
        for sym in data_dict
    }
    port_ret = (held_weights * returns_df).sum(axis=1) - (turnover.sum(axis=1) * fee_rate)
    all_metrics["DANH MỤC (TỔNG)"] = _calc_full_metrics(weights_oos.index, port_ret, rf_rate)

    print("\n" + pd.DataFrame(all_metrics).to_string())