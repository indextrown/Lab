# ==========================
# 환경변수 로딩 (.env)
#      ↓
# API 연결 및 초기값 설정
#      ↓
# 4시간봉 데이터 → RSI 계산
#      ↓
# 실시간 잔고 조회 (KRW, BTC, 평균단가)
#      ↓
# [조건 검사]
#   └─ RSI ≤ 30  → 매수 실행(20프로씩)
#   └─ RSI ≥ 70
#        └─ 손실/본전 → 전량 매도
#        └─ 수익 ≥ 5% → 전량 매도
#      ↓
# 모든 결과 Gmail 전송
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

# ==========================
# 🔧 설정값
# ==========================
TICKER = "KRW-ETH"
INTERVAL = "minute240"
RSI_PERIOD = 14
BUY_THRESHOLD = 30
SELL_THRESHOLD = 70
PARTIAL_SELL_PROFIT = 5  # % 수익 기준 전량 매도
FEE = 0.0005
BUY_RATIO = 0.2
MIN_TRADE = 5000
GMAIL_ADDRESS = "indextrown@gmail.com"
TO_EMAIL = ["indextrown@gmail.com","wjs9643@naver.com"]

# ==========================
# 🔐 API 초기화
# ==========================
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY") 
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

# ==========================
# 📬 메일 전송 함수
# ==========================
def send_gmail(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = ", ".join(TO_EMAIL)   # ✅ 리스트 → 문자열
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        # print("✅ 메일 전송 완료")
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
    krw = next((float(x['balance']) for x in balances if x['currency'] == 'KRW'), 0)
    btc = next((float(x['balance']) for x in balances if x['currency'] == 'BTC'), 0)
    avg_price = next((float(x['avg_buy_price']) for x in balances if x['currency'] == 'BTC'), 0)
    return krw, btc, avg_price

# ==========================
# 🚀 메인 실행
# ==========================
def main():
    print()
    # print(f"\n📌 [실전 매매 봇 실행]")
    # print(f"- 종목: {TICKER} | 간격: {INTERVAL} | RSI 기준: {RSI_PERIOD}")

    df = pyupbit.get_ohlcv(TICKER, interval=INTERVAL)
    if df is None or len(df) < RSI_PERIOD + 1:
        print("❌ OHLCV 데이터 부족")
        return

    df["RSI"] = get_rsi(df, RSI_PERIOD)
    rsi = df["RSI"].iloc[-1]
    prev_rsi = df["RSI"].iloc[-2]
    price = df["close"].iloc[-1]
    candle_time = df.index[-1]
    candle_end_time = candle_time + timedelta(hours=4)

    krw, btc, avg_price = get_account_status()

    # print(f"- 기준 봉: {candle_time} ~ {candle_end_time}")
    # print(f"- 기준 RSI: {rsi:.2f} | 현재가: {price:.0f} | 보유 KRW: {krw:,.0f} | BTC: {btc}")

    # ✅ 매수
    if rsi <= BUY_THRESHOLD and krw > MIN_TRADE:
        invest_amount = krw * BUY_RATIO
        if invest_amount >= MIN_TRADE:
            try:
                result = upbit.buy_market_order(TICKER, invest_amount)
                msg = textwrap.dedent(f"""
                [매수 성공]
                - 기준 봉: {candle_time} ~ {candle_end_time}
                - 기준 RSI: {rsi:.2f}
                - 이전 봉 RSI: {prev_rsi:.2f}
                - 현재가: {price:,.0f}원
                - 매수 금액: {invest_amount:,.0f}원
                - 주문 결과: {result}
                - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """)
                print(msg)
                send_gmail("[매수 성공]", msg)
            except Exception as e:
                send_gmail("[매수 실패]", f"에러: {e}")

    # ✅ 매도
    # if RSI가 70 이상이라면
    #   if 수익률이 음수이면 전체 매도(손절)
    #   if 수익률이 25% 이상이면 절반 시장가 매도   
    # 
    elif rsi >= SELL_THRESHOLD and btc > 0:
        profit_rate = (price - avg_price) / avg_price * 100
        hold_value = btc * price

        # 손실 or 본전 → 전량 매도
        if profit_rate <= 0:
            try:
                result = upbit.sell_market_order(TICKER, btc)
                msg = textwrap.dedent(f"""
                [전량 매도]
                - 기준 봉: {candle_time} ~ {candle_end_time}
                - 기준 RSI: {rsi:.2f}
                - 수익률: {profit_rate:.2f}%
                - 매도 금액: {hold_value:,.0f}원
                - 주문 결과: {result}
                - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """)
                print(msg)
                send_gmail("[전량 매도]", msg)
            except Exception as e:
                send_gmail("[전량 매도 실패]", f"에러: {e}")

        # 익절 5% 이상 → 전량 매도
        elif profit_rate >= PARTIAL_SELL_PROFIT:
            if hold_value >= MIN_TRADE:
                try:
                    result = upbit.sell_market_order(TICKER, btc)
                    msg = textwrap.dedent(f"""
                    [전량 매도 5% (익절)]
                    - 기준 봉: {candle_time} ~ {candle_end_time}
                    - 기준 RSI: {rsi:.2f}
                    - 수익률: {profit_rate:.2f}%
                    - 매도 금액: {hold_value:,.0f}원
                    - 주문 결과: {result}
                    - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    """)
                    print(msg)
                    send_gmail("[전량 매도]", msg)
                except Exception as e:
                    send_gmail("[전량 매도 실패]", f"에러: {e}")
    else:
        msg = textwrap.dedent(f"""
        [매수 실패]
        - 기준 봉: {candle_time} ~ {candle_end_time}
        - 기준 RSI: {rsi:.2f}
        - 이전 봉 RSI: {prev_rsi:.2f}
        - 매수 조건 미충족: RSI 값이 {BUY_THRESHOLD} 초과
        - 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """)
        print(msg)
        # send_gmail("[매수 실패]", msg)


if __name__ == "__main__":
    main()


