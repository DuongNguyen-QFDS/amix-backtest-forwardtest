# Hệ Thống Backtest - Forwardtest thông qua API AmiX

Hệ thống hỗ trợ giao dịch định lượng (Quantitative Trading) khép kín bằng Python, kết nối trực tiếp dữ liệu lịch sử cuối ngày (EOD) từ **AmiX / AmiBroker**, hỗ trợ trực quan hóa dữ liệu, kiểm thử quá khứ (Backtest) với bộ 11 chỉ số quản trị rủi ro và chạy giả lập thời gian thực (Forward Test).

## Kiến Trúc Dự Án

Hệ thống được thiết kế theo mô hình **Single Entry Point** (`main.py`) và **Single Source of Truth** (`module/strategy.py`). Mọi thay đổi về rổ cổ phiếu, tham số hoặc thuật toán phân bổ vốn chỉ cần chỉnh sửa duy nhất tại `module/strategy.py`.

```text
ProjectApply/
├── main.py                  # Bảng điều khiển trung tâm (Entry point duy nhất)
├── module/
│   ├── strategy.py          # Cấu hình rổ cổ phiếu, tham số & thuật toán chiến lược
│   ├── dnse_reader.py       # Kết nối và đọc dữ liệu EOD từ thư mục AmiX
│   ├── data_viz.py          # Trích xuất dữ liệu, chuẩn hóa và vẽ biểu đồ phân bổ vốn
│   ├── backtest.py          # Chạy kiểm thử quá khứ & tính 11 chỉ số hiệu suất/rủi ro
│   └── forwardtest.py       # Theo dõi dữ liệu mới và xuất khuyến nghị tỷ trọng hàng ngày
├── data/                    # Thư mục lưu dữ liệu thô (*_raw.csv), biểu đồ và log lệnh
├── pyproject.toml           # Quản lý thư viện dự án (uv)
└── README.md

Lưu ý: Việc đăng kí sử dụng AmiX của DNSE là bắt buộc để khởi chạy dự án, đồng thời phải nhập Smart OTP và đăng kí lightfast API của AmiX