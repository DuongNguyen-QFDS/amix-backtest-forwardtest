import sys
import io
import os

# Cấu hình UTF-8 cho Terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Thêm thư mục 'module' vào đường dẫn tìm kiếm của Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.join(BASE_DIR, "module")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# Import các module từ thư mục module/
from strategy import SYMBOLS, PARAMS
from data_viz import run_data_viz
from backtest import run_backtest
from forwardtest import run_forward_test

def show_menu():
    print("\n==============================================")
    print("   HỆ THỐNG QUANT TRADING - DỮ LIỆU AMIX")
    print(f"   Rổ cổ phiếu hiện tại: {SYMBOLS}")
    print(f"   Tham số chiến lược: {PARAMS}")
    print("==============================================")
    print("1. Tải dữ liệu từ AmiX & Vẽ biểu đồ (Data & Viz)")
    print("2. Chạy kiểm thử quá khứ (Backtest)")
    print("3. Chạy trọn gói: Tải dữ liệu -> Backtest (1 + 2)")
    print("4. Chạy giả lập thời gian thực (Forward Test)")
    print("0. Thoát")
    print("==============================================")

def main():
    # Hỗ trợ chạy nhanh qua tham số dòng lệnh: VD `uv run main.py all`
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "viz":
            run_data_viz()
        elif cmd == "backtest":
            run_backtest()
        elif cmd == "all":
            run_data_viz()
            run_backtest()
        elif cmd == "forward":
            run_forward_test(poll_interval_sec=300)
        return

    # Chế độ Menu tương tác
    while True:
        show_menu()
        choice = input("Chọn chức năng (0-4): ").strip()

        if choice == "1":
            run_data_viz()
        elif choice == "2":
            run_backtest()
        elif choice == "3":
            run_data_viz()
            run_backtest()
        elif choice == "4":
            run_forward_test(poll_interval_sec=300)
        elif choice == "0":
            print("Đã thoát hệ thống.")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng nhập từ 0 đến 4.")

if __name__ == "__main__":
    main()