import pyupbit
import datetime

# 시작일과 종료일을 선택하여 고가/시가/저가/종가/거래량을 DataFrame으로 반환

# -----------------------------
# 1) 시작일과 종료일을 설정하여 OHLCV 기간 조회 함수
# -----------------------------
def get_ohlcv_range(ticker, start, end, interval="day", period=14):
    # RSI 계산을 위해 과거 데이터 확보
    start_buffer = start - datetime.timedelta(days=period * 2)

    count = 200
    df = None

    while True:
        df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
        if df is None:
            raise Exception("데이터를 가져올 수 없습니다.")

        if df.index.min() <= start_buffer:
            break
        
        count *= 2
        if count > 5000:
            break

    df_full = df[(df.index >= start_buffer) & (df.index <= end)]
    df_clean = df[(df.index >= start) & (df.index <= end)]

    return df_clean, df_full


# -----------------------------
# 2) RSI 계산 함수
# -----------------------------
def compute_rsi(series, period=14):
    delta = series.diff()

    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    # 핵심: Wilder 방식 → ewm(com=period-1)
    ma_up = up.ewm(com=period - 1, min_periods=period).mean()
    ma_down = down.ewm(com=period - 1, min_periods=period).mean()

    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi
