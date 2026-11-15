import numpy as np
import pandas as pd

# 1. RỔ CỔ PHIẾU
SYMBOLS = ["TCB"]

# 2. THAM SỐ CHIẾN LƯỢC (ĐIỀU CHỈNH TRỰC TIẾP TẠI ĐÂY)
PARAMS = {
    "start_date": "2006-07-12",      
    "end_date": "2026-11-13",
    "vol_target": 0.15,      # 15%
    "vol_window": 30,        # 30 days
    "max_leverage": 1.0,     # Thử đổi lên 1.5 hoặc 2.0 nếu web cho phép đòn bẩy
    "rebalance_days": 1,     # Tái cân bằng hàng ngày (hoặc đổi thành 21 nếu tái cân bằng theo tháng)
    "max_weight": 1.0,       # Bỏ giới hạn trần 50%
    "fee_rate": 0.0,         # Đặt 0% phí để so sánh thuần thuật toán
    "rf_rate": 0.05          # Lãi suất phi rủi ro 5%/năm (hoặc 0.0 tùy cài đặt web)
}

# 3. HÀM TẠO TỶ TRỌNG DANH MỤC (INVERSE VOLATILITY + VOLATILITY TARGETING)
def generate_weights(data_dict):
    win = PARAMS["vol_window"]
    prices_dict = {}

    for sym, df in data_dict.items():
        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").drop_duplicates("date").set_index("date")
        prices_dict[sym] = data["close"]

    prices_df = pd.DataFrame(prices_dict).sort_index()
    returns_df = prices_df.pct_change()

    # Bước 1: Tính tỷ trọng cơ sở theo Inverse Volatility (đợi đủ cửa sổ `win` phiên)
    vol_df = returns_df.rolling(window=win, min_periods=win).std()
    inv_vol_df = 1.0 / vol_df.replace(0, np.nan)
    base_weights = inv_vol_df.div(inv_vol_df.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    max_w = PARAMS.get("max_weight", 1.0)
    if max_w < 1.0:
        for _ in range(3):
            base_weights = base_weights.clip(upper=max_w)
            base_weights = base_weights.div(base_weights.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    # Bước 2: Áp dụng Volatility Target bằng Ma trận hiệp phương sai (Covariance Matrix)
    vol_target = PARAMS.get("vol_target")
    if vol_target is not None and vol_target > 0:
        weights = pd.DataFrame(0.0, index=base_weights.index, columns=base_weights.columns)
        max_lev = PARAMS.get("max_leverage", 1.0)

        for i in range(win, len(base_weights)):
            w = base_weights.iloc[i].values
            if w.sum() == 0:
                continue

            # Ma trận hiệp phương sai quy đổi năm trong cửa sổ 30 phiên gần nhất
            window_rets = returns_df.iloc[i - win + 1 : i + 1].fillna(0)
            cov_matrix = window_rets.cov().values * 252
            port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))

            if port_vol > 0:
                scalar = min(max_lev, vol_target / port_vol)
                weights.iloc[i] = w * scalar
    else:
        weights = base_weights

    # Bước 3: Áp dụng chu kỳ tái cân bằng
    reb = PARAMS.get("rebalance_days", 1)
    if reb > 1:
        rebalanced = pd.DataFrame(np.nan, index=weights.index, columns=weights.columns)
        rebalanced.iloc[::reb] = weights.iloc[::reb]
        weights = rebalanced.ffill().fillna(0)

    return weights