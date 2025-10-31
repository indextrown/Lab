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

# ==========================
# RSI 트레이딩 봇 + 자산/RSI 로그 저장
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
INTERVAL = "minute240"  # 4시간봉
RSI_PERIOD = 14
BUY_THRESHOLD = 30
SELL_THRESHOLD = 70
SELL_PROFIT = 5  # % 수익 기준 전량 매도
FEE = 0.0005
BUY_RATIO = 0.2
MIN_TRADE = 5000
GMAIL_ADDRESS = "indextrown@gmail.com"
TO_EMAIL = ["indextrown@gmail.com", "wjs9643@naver.com"]

ASSET_LOG_PATH = "asset_log.csv"
TRADE_LOG_PATH = "trade_log.txt"

# ==========================
# 🔐 API 초기화
# ==========================
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
GMAIL_APP_PASSWORD = (os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "")

upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)
BASE_COIN = TICKER.split("-")[1]

# ==========================
# 📬 메일 전송 함수
# ==========================
def send_gmail(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD):
        print("✉️ Gmail 설정이 없어서 메일 전송 생략")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = ", ".join(TO_EMAIL)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
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
# 💰 잔고 조회 함수
# ==========================
def get_account_status():
    balances = upbit.get_balances()
    krw = next((float(x["balance"]) for x in balances if x["currency"] == "KRW"), 0.0)
    coin_amt = next((float(x["balance"]) for x in balances if x["currency"] == BASE_COIN), 0.0)
    avg_price = next((float(x["avg_buy_price"]) for x in balances if x["currency"] == BASE_COIN), 0.0)
    return krw, coin_amt, avg_price

# ==========================
# 📊 로그 함수 (RSI 포함)
# ==========================
def log_asset(now_str, price, krw, coin_amt, rsi):
    total_asset = krw + coin_amt * price
    line = f"{now_str},{price},{krw},{coin_amt},{total_asset},{rsi:.2f}\n"
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

    if isnan(rsi) or isnan(prev_rsi):
        print("❌ RSI 계산 NaN 발생")
        return

    krw, coin_amt, avg_price = get_account_status()

    # ✅ 매수 조건
    if rsi <= BUY_THRESHOLD and krw > MIN_TRADE:
        invest_amount = krw * BUY_RATIO
        if invest_amount >= MIN_TRADE:
            try:
                result = upbit.buy_market_order(TICKER, invest_amount)
                msg = textwrap.dedent(f"""
                [매수 성공]
                - 종목: {TICKER}
                - 기준 봉: {candle_time} ~ {candle_end_time}
                - RSI: 현재 {rsi:.2f} / 이전 {prev_rsi:.2f}
                - 매수 금액: {invest_amount:,.0f}원
                - 현재가: {price:,.0f}원
                - 주문 결과: {result}
                - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """)
                print(msg)
                send_gmail("[매수 성공]", msg)
                log_trade(msg)
            except Exception as e:
                send_gmail("[매수 실패]", f"에러: {e}")

    # ✅ 매도 조건
    elif rsi >= SELL_THRESHOLD and coin_amt > 0:
        profit_rate = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
        hold_value = coin_amt * price

        if profit_rate <= 0:
            try:
                result = upbit.sell_market_order(TICKER, coin_amt)
                msg = textwrap.dedent(f"""
                [전량 매도 (본전/손실)]
                - RSI: {rsi:.2f}
                - 수익률: {profit_rate:.2f}%
                - 금액: {hold_value:,.0f}원
                """)
                print(msg)
                send_gmail("[전량 매도]", msg)
                log_trade(msg)
            except Exception as e:
                send_gmail("[전량 매도 실패]", f"에러: {e}")

        elif profit_rate >= SELL_PROFIT:
            try:
                result = upbit.sell_market_order(TICKER, coin_amt)
                msg = textwrap.dedent(f"""
                [전량 매도 (익절 {profit_rate:.2f}%)]
                - RSI: {rsi:.2f}
                - 금액: {hold_value:,.0f}원
                """)
                print(msg)
                send_gmail("[익절 매도]", msg)
                log_trade(msg)
            except Exception as e:
                send_gmail("[익절 매도 실패]", f"에러: {e}")

    else:
        print(f"[대기] RSI={rsi:.2f}, 가격={price:,.0f}")

    # ✅ 자산 로그 (RSI 포함)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    krw_now, coin_now, _ = get_account_status()
    total_asset = log_asset(now_str, price, krw_now, coin_now, rsi)
    print(f"🧾 자산 로그 저장: {now_str}, 총자산 {total_asset:,.0f}원, RSI {rsi:.2f}")

if __name__ == "__main__":
    main()
