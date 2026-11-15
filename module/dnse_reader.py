import os
import struct
import pandas as pd

class DNSEDataReader:
    """
    Tiện ích đọc dữ liệu chứng khoán trực tiếp từ thư mục dữ liệu cục bộ của Ami X (DNSE).
    Hỗ trợ đọc dữ liệu EOD (End of Day) và Intraday Tick bằng cách giải mã định dạng binary MetaStock.
    """
    def __init__(self, data_dir=r"D:\AmiXDNSE"):
        self.data_dir = data_dir

    def _fmsbin2ieee(self, data: bytes) -> float:
        """Chuyển đổi định dạng số thực Microsoft Binary (MBF) sang IEEE 754 float."""
        val = struct.unpack("<I", data)[0]
        if val == 0:
            return 0.0
        man = struct.unpack("<H", data[2:4])[0]
        if man == 0:
            return 0.0
        result = bytearray(data)
        result[2] = ((man >> 1) & 0x80) | (man & 0xff)
        result[3] = (man & 0x80) | (((man >> 9) - 1) & 0xff)
        return struct.unpack("<f", bytes(result))[0]

    def _float2date(self, val: float) -> str:
        """Chuyển đổi float đại diện cho ngày dạng YYYYMMDD sang chuỗi định dạng YYYY-MM-DD."""
        date_num = int(19000000 + round(val))
        date_str = str(date_num)
        if len(date_str) < 8:
            return date_str
        return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"

    def _float2time(self, val: float) -> str:
        """Chuyển đổi float đại diện cho thời gian dạng HHMMSS sang chuỗi định dạng HH:MM:SS."""
        time_num = int(round(val))
        time_str = f"{time_num:06d}"
        if len(time_str) >= 6:
            return f"{time_str[-6:-4]}:{time_str[-4:-2]}:{time_str[-2:]}"
        return time_str

    def get_intraday_tick(self, symbol: str) -> pd.DataFrame:
        """
        Đọc dữ liệu Intraday Tick (thời gian thực/trong ngày) của mã cổ phiếu.
        Dữ liệu được lấy từ thư mục cache/intraday của Ami X.
        
        Args:
            symbol (str): Mã chứng khoán (ví dụ: 'FPT', 'VIC', 'HPG').
            
        Returns:
            pd.DataFrame: DataFrame chứa các cột ['datetime', 'price', 'volume'].
        """
        filepath = os.path.join(self.data_dir, "intraday", "cache", "intraday", f"{symbol}.DAT")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Không tìm thấy tệp dữ liệu Tick cho mã {symbol} tại: {filepath}")

        with open(filepath, "rb") as f:
            data = f.read()

        group = 16  # Định dạng 4 trường (mỗi trường 4 byte): Date, Time, Price, Volume
        total_rows = len(data) // group
        
        records = []
        for i in range(1, total_rows):
            buf = data[group*i : group*(group+1)] # Wait! There is a small bug here! It should be group*i : group*(i+1)
            # Ah! Let's check my previous code: group*i : group*(group+1). Oh! That was a typo.
            # In my previous code: buf = data[group*i : group*(i+1)]. Let me write it correctly as: group*i : group*(i+1)
            buf = data[group*i : group*(i+1)]
            date_float = self._fmsbin2ieee(buf[0:4])
            time_float = self._fmsbin2ieee(buf[4:8])
            price = self._fmsbin2ieee(buf[8:12])
            volume = self._fmsbin2ieee(buf[12:16])
            
            date_str = self._float2date(date_float)
            time_str = self._float2time(time_float)
            
            records.append({
                "datetime": f"{date_str} {time_str}",
                "price": price,
                "volume": int(volume)
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def _parse_master_files(self, eod_dir: str) -> dict:
        """Quét đệ quy các file MASTER/EMASTER để tìm ánh xạ mã cổ phiếu sang tên file F{n}.DAT tương ứng."""
        symbol_map = {}
        for root, dirs, files in os.walk(eod_dir):
            # 1. Đọc file MASTER (độ dài bản ghi 53 byte)
            if "MASTER" in files:
                master_path = os.path.join(root, "MASTER")
                with open(master_path, "rb") as f:
                    data = f.read()
                records = len(data) // 53
                for i in range(1, records):
                    buf = data[53*i : 53*(i+1)]
                    file_num = buf[0]
                    fields = buf[4]
                    symbol = buf[36:51].split(b"\x00")[0].decode("ascii", errors="ignore").strip()
                    clean_symbol = symbol.replace("_AC", "")
                    filepath = os.path.join(root, f"F{file_num}.DAT")
                    
                    if os.path.exists(filepath):
                        symbol_map[clean_symbol] = {
                            "filepath": filepath,
                            "fields": fields
                        }
            # 2. Đọc file EMASTER (độ dài bản ghi 192 byte)
            if "EMASTER" in files:
                emaster_path = os.path.join(root, "EMASTER")
                with open(emaster_path, "rb") as f:
                    data = f.read()
                records = len(data) // 192
                for i in range(1, records):
                    buf = data[192*i : 192*(i+1)]
                    file_num = buf[2]
                    fields = buf[6]
                    symbol = buf[11:26].split(b"\x00")[0].decode("ascii", errors="ignore").strip()
                    clean_symbol = symbol.replace("_AC", "")
                    filepath = os.path.join(root, f"F{file_num}.DAT")
                    
                    if os.path.exists(filepath):
                        if clean_symbol not in symbol_map or symbol_map[clean_symbol]["fields"] == 0:
                            symbol_map[clean_symbol] = {
                                "filepath": filepath,
                                "fields": fields if fields > 0 else 7
                            }
        return symbol_map

    def get_eod(self, symbol: str) -> pd.DataFrame:
        """
        Đọc dữ liệu lịch sử ngày (EOD - End of Day) của mã cổ phiếu.
        Ưu tiên đọc từ tệp cache lịch sử đầy đủ (.MWD) nếu có, nếu không sẽ quét chỉ mục MASTER/EMASTER.
        
        Args:
            symbol (str): Mã chứng khoán.
            
        Returns:
            pd.DataFrame: DataFrame chứa các cột ['date', 'open', 'high', 'low', 'close', 'volume', 'oi'].
        """
        # Ưu tiên 1: Đọc từ cache lịch sử EOD đầy đủ của Ami X (được lưu dưới dạng .MWD)
        cache_filepath = os.path.join(self.data_dir, "intraday", "cache", "eod", f"{symbol}.MWD")
        if os.path.exists(cache_filepath):
            filepath = cache_filepath
            fields = 7
        else:
            # Ưu tiên 2: Quét từ MASTER/EMASTER
            eod_dir = os.path.join(self.data_dir, "eod")
            symbol_map = self._parse_master_files(eod_dir)
            if symbol not in symbol_map:
                raise FileNotFoundError(f"Không tìm thấy dữ liệu lịch sử EOD cho mã {symbol} trên đĩa.")
            meta = symbol_map[symbol]
            filepath = meta["filepath"]
            fields = meta["fields"]
        
        with open(filepath, "rb") as f:
            data = f.read()
            
        group = fields * 4
        total_rows = len(data) // group
        
        records = []
        for i in range(1, total_rows):
            buf = data[group*i : group*(i+1)]
            date_float = self._fmsbin2ieee(buf[0:4])
            date_str = self._float2date(date_float)
            
            row_data = [date_str]
            for j in range(4, group, 4):
                row_data.append(self._fmsbin2ieee(buf[j : j+4]))
                
            records.append({
                "date": row_data[0],
                "open": row_data[1] if len(row_data) > 1 else 0.0,
                "high": row_data[2] if len(row_data) > 2 else 0.0,
                "low": row_data[3] if len(row_data) > 3 else 0.0,
                "close": row_data[4] if len(row_data) > 4 else 0.0,
                "volume": int(row_data[5]) if len(row_data) > 5 else 0,
                "oi": int(row_data[6]) if len(row_data) > 6 else 0
            })
            
        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

if __name__ == "__main__":
    reader = DNSEDataReader()
    try:
        fpt_eod = reader.get_eod("FPT")
        print("Đọc dữ liệu EOD thành công!")
        print(f"Tổng số ngày đọc được: {len(fpt_eod)}")
        print(fpt_eod.tail(105))
    except Exception as e:
        print("Lỗi đọc EOD:", e)
