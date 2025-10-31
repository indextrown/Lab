# ==========================
# 환경변수 로딩 (.env)
#      ↓
# API 연결 및 초기값 설정
#      ↓
# 4시간봉 데이터 → RSI 계산
#      ↓
# 실시간 잔고 조회 (KRW, COIN, 평균단가)
#      ↓
# [조건 검사]
#   └─ RSI ≤ 30  → 매수 실행(20프로씩)
#   └─ RSI ≥ 70
#        └─ 손실/본전 → 전량 매도
#        └─ 수익 ≥ 5% → 전량 매도
#      ↓
# 모든 결과 Gmail 전송 + 자산 로그 저장(asset_log.csv)
# ==========================

import pyupbit
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import textwrap
from math import isnan

# ==========================
# 🔧 설정값
# ==========================
TICKER = "KRW-ETH"
INTERVAL = "minute240"
RSI_PERIOD = 14
BUY_THRESHOLD = 30
SELL_THRESHOLD = 70
PARTIAL_SELL_PROFIT = 5  # % 수익 기준 전량 매도
FEE = 0.0005             # 필요시 체결가에 반영
BUY_RATIO = 0.2
MIN_TRADE = 5000
GMAIL_ADDRESS = "indextrown@gmail.com"
TO_EMAIL = ["indextrown@gmail.com", "wjs9643@naver.com"]

ASSET_LOG_PATH = "asset_log.csv"
TRADE_LOG_PATH = "trade_log.txt"   # (선택)

# ==========================
# 🔐 API 초기화
# ==========================
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
GMAIL_APP_PASSWORD = (os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "")

upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

# 베이스 코인 심볼 (KRW-ETH -> ETH)
BASE_COIN = TICKER.split("-")[1]

# ==========================
# 📬 메일 전송 함수
# ==========================
def send_gmail(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD):
        print("✉️  Gmail 설정이 없어서 메일 전송 생략")
        return
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = ", ".join(TO_EMAIL)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("❌ 메일 전송 실패:", e)

# ==========================
# 📈 RSI 계산 함수
# ==========================
def get_rsi(ohlcv, period=14):
    delta = ohlcv["close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, min_periods=period).mean()
    ma_down = down.ewm(com=period - 1, min_periods=period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

# ==========================
# 💰 잔고 조회 함수 (티커 베이스 코인 반영)
# ==========================
def get_account_status():
    balances = upbit.get_balances()
    krw = next((float(x['balance']) for x in balances if x['currency'] == 'KRW'), 0.0)
    coin_amt = next((float(x['balance']) for x in balances if x['currency'] == BASE_COIN), 0.0)
    avg_price = next((float(x['avg_buy_price']) for x in balances if x['currency'] == BASE_COIN), 0.0)
    return krw, coin_amt, avg_price

def log_asset(now_str, price, krw, coin_amt):
    total_asset = krw + coin_amt * price
    line = f"{now_str},{price},{krw},{coin_amt},{total_asset}\n"
    with open(ASSET_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    return total_asset

def log_trade(text):
    try:
        with open(TRADE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(text.strip() + "\n")
    except Exception:
        pass

# ==========================
# 🚀 메인 실행
# ==========================
def main():
    df = pyupbit.get_ohlcv(TICKER, interval=INTERVAL)
    if df is None or len(df) < RSI_PERIOD + 1:
        print("❌ OHLCV 데이터 부족")
        return

    df["RSI"] = get_rsi(df, RSI_PERIOD)
    rsi = float(df["RSI"].iloc[-1])
    prev_rsi = float(df["RSI"].iloc[-2])
    price = float(df["close"].iloc[-1])
    candle_time = df.index[-1]
    candle_end_time = candle_time + timedelta(hours=4)

    # NaN 방어
    if rsi != rsi or prev_rsi != prev_rsi:  # NaN 체크
        print("❌ RSI 계산 NaN 발생")
        return

    krw, coin_amt, avg_price = get_account_status()

    # ✅ 매수
    if rsi <= BUY_THRESHOLD and krw > MIN_TRADE:
        invest_amount = krw * BUY_RATIO
        if invest_amount >= MIN_TRADE:
            try:
                # 수수료를 반영하려면 invest_amount * (1 - FEE) 정도로 조정 가능
                result = upbit.buy_market_order(TICKER, invest_amount)
                msg = textwrap.dedent(f"""
                [매수 성공]
                - 종목: {TICKER}
                - 기준 봉: {candle_time} ~ {candle_end_time}
                - RSI: 현재 {rsi:.2f} / 이전 {prev_rsi:.2f} / 기준 ≤ {BUY_THRESHOLD}
                - 현재가: {price:,.0f}원
                - 매수 금액: {invest_amount:,.0f}원
                - 주문 결과: {result}
                - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """)
                print(msg)
                send_gmail("[매수 성공]", msg)
                log_trade(msg)
            except Exception as e:
                send_gmail("[매수 실패]", f"에러: {e}")

    # ✅ 매도
    elif rsi >= SELL_THRESHOLD and coin_amt > 0:
        profit_rate = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
        hold_value = coin_amt * price

        # 손실 or 본전 → 전량 매도
        if profit_rate <= 0:
            try:
                result = upbit.sell_market_order(TICKER, coin_amt)
                msg = textwrap.dedent(f"""
                [전량 매도]
                - 종목: {TICKER}
                - 기준 봉: {candle_time} ~ {candle_end_time}
                - RSI: {rsi:.2f} / 기준 ≥ {SELL_THRESHOLD}
                - 수익률: {profit_rate:.2f}%
                - 매도 금액: {hold_value:,.0f}원
                - 주문 결과: {result}
                - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """)
                print(msg)
                send_gmail("[전량 매도]", msg)
                log_trade(msg)
            except Exception as e:
                send_gmail("[전량 매도 실패]", f"에러: {e}")

        # 익절 5% 이상 → 전량 매도
        elif profit_rate >= PARTIAL_SELL_PROFIT:
            if hold_value >= MIN_TRADE:
                try:
                    result = upbit.sell_market_order(TICKER, coin_amt)
                    msg = textwrap.dedent(f"""
                    [전량 매도 5% (익절)]
                    - 종목: {TICKER}
                    - 기준 봉: {candle_time} ~ {candle_end_time}
                    - RSI: {rsi:.2f} / 기준 ≥ {SELL_THRESHOLD}
                    - 수익률: {profit_rate:.2f}%
                    - 매도 금액: {hold_value:,.0f}원
                    - 주문 결과: {result}
                    - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    """)
                    print(msg)
                    send_gmail("[전량 매도]", msg)
                    log_trade(msg)
                except Exception as e:
                    send_gmail("[전량 매도 실패]", f"에러: {e}")

    else:
        # 매수/매도 조건 미충족 대기
        msg = textwrap.dedent(f"""
        [대기]
        - 종목: {TICKER}
        - 기준 봉: {candle_time} ~ {candle_end_time}
        - RSI: 현재 {rsi:.2f} / 이전 {prev_rsi:.2f}
        - 조건: 매수 ≤ {BUY_THRESHOLD}, 매도 ≥ {SELL_THRESHOLD}
        - 현재가: {price:,.0f}원
        - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """)
        print(msg)

    # ✅ 매 실행마다 자산 스냅샷 로그 (그래프용)
    # 1열: 실행 시각
    # 2열: 가격 (ETH 현재가)
    # 3열: 보유 KRW
    # 4열: 보유 ETH 수량
    # 5열: 총자산(원화 기준)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    krw_now, coin_now, _ = get_account_status()
    total_asset = log_asset(now_str, price, krw_now, coin_now)
    print(f"🧾 자산 로그 저장: {now_str}, 총자산 {total_asset:,.0f}원")

if __name__ == "__main__":
    main()
