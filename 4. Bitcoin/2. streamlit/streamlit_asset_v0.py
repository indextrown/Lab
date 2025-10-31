# streamlit run streamlit_asset.py
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="내 자산 추이", layout="wide")
st.title("💰 내 자산 추이 그래프")

# CSV 불러오기
try:
    df = pd.read_csv(
        "asset_log.csv",
        names=["time", "price", "krw", "coin", "asset"]
    )
    df["time"] = pd.to_datetime(df["time"])
except FileNotFoundError:
    st.error("⚠️ asset_log.csv 파일이 없습니다.")
    st.stop()

# 중복 제거 (같은 시간대 로그 중복 방지)
df = df.drop_duplicates(subset=["time"], keep="last").sort_values("time")

# 최근 자산 데이터
latest_asset = df["asset"].iloc[-1]
start_asset = df["asset"].iloc[0]
change_pct = (latest_asset / start_asset - 1) * 100

# KPI 영역
col1, col2, col3 = st.columns(3)
col1.metric("📆 데이터 개수", f"{len(df)}개")
col2.metric("💰 현재 총 자산", f"{latest_asset:,.0f} 원")
col3.metric("📈 변화율", f"{change_pct:+.2f}%")

# 📊 자산 추이 그래프
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["time"],
    y=df["asset"],
    mode="lines+markers",
    name="총자산(원)",
    line=dict(width=2)
))
fig.update_layout(
    title="총자산 추이",
    xaxis_title="시간",
    yaxis_title="총자산 (KRW)",
    hovermode="x unified",
    height=500,
    margin=dict(l=20, r=20, t=60, b=40)
)
st.plotly_chart(fig, use_container_width=True)

# 📈 ETH 가격 추이도 함께 보기 (선택)
with st.expander("🪙 ETH 가격 추이 보기"):
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["price"],
        mode="lines",
        name="ETH 가격(원)",
        line=dict(color="orange", width=2)
    ))
    price_fig.update_layout(
        title="ETH 가격 변화",
        xaxis_title="시간",
        yaxis_title="ETH 가격 (KRW)",
        height=400
    )
    st.plotly_chart(price_fig, use_container_width=True)

# 최근 로그 표시
st.subheader("📋 최근 자산 로그")
st.dataframe(df.tail(10))
