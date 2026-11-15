import os
import matplotlib.pyplot as plt
from dnse_reader import DNSEDataReader
from strategy import SYMBOLS, generate_weights

def run_data_viz():
    os.makedirs("data", exist_ok=True)
    reader = DNSEDataReader()
    data_dict = {}

    for sym in SYMBOLS:
        df = reader.get_eod(sym)
        df.to_csv(f"data/{sym}_raw.csv", index=False)
        data_dict[sym] = df

    # Gọi strategy.py để tính tỷ trọng cho toàn bộ rổ
    weights_df = generate_weights(data_dict)
    weights_df.to_csv("data/portfolio_weights.csv")

    # Vẽ biểu đồ giá và tỷ trọng vốn phân bổ theo thời gian
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for sym in SYMBOLS:
        s_df = data_dict[sym].set_index("date")
        norm_price = s_df["close"] / s_df["close"].iloc[0] * 100
        ax1.plot(norm_price.index, norm_price, label=sym)
    ax1.set_title("Biến động giá chuẩn hóa (Gốc = 100)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    weights_df.plot.area(ax=ax2, alpha=0.7)
    ax2.set_title("Tỷ trọng phân bổ vốn theo chiến lược (%)")
    ax2.set_ylabel("Tỷ trọng (0 - 1)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("data/strategy_overview.png", dpi=150)
    plt.close()
    print(f"[OK] Đã tải {len(SYMBOLS)} mã và xuất biểu đồ tại data/strategy_overview.png")