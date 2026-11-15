import os, time
from datetime import datetime
import pandas as pd
from dnse_reader import DNSEDataReader
from strategy import SYMBOLS, generate_weights

def run_forward_test(poll_interval_sec=300):
    reader = DNSEDataReader()
    last_date = None
    print(f"Đang chạy Forward Test cho rổ {SYMBOLS}. Nhấn Ctrl+C để dừng.")

    while True:
        try:
            data_dict = {sym: reader.get_eod(sym) for sym in SYMBOLS}
            weights_df = generate_weights(data_dict)
            curr_date = str(weights_df.index[-1])[:10]

            if curr_date != last_date:
                last_date = curr_date
                latest_w = (weights_df.iloc[-1] * 100).round(2)
                print(f"[{curr_date}] Tỷ trọng khuyến nghị: " + " | ".join([f"{k}: {v}%" for k, v in latest_w.items()]))
                
                os.makedirs("data", exist_ok=True)
                row = pd.DataFrame([{"Date": curr_date, **latest_w.to_dict()}])
                row.to_csv("data/forward_log.csv", mode="a", header=not os.path.exists("data/forward_log.csv"), index=False)

            time.sleep(poll_interval_sec)
        except KeyboardInterrupt:
            break