# import streamlit as st

# st.set_page_config(page_title="PopPang 관리자 페이지", layout="wide")

# st.title("🎛️ PopPang 관리자 페이지")
# st.write("좌측 메뉴에서 관리할 항목을 선택하세요.")
# st.markdown("---")

# st.info("👥 사용자 관리 또는 🎪 팝업 관리 메뉴를 선택하면 각 항목을 조회/수정할 수 있습니다.")



# ------------------------------------------------------------
# ✅ 0. 비밀번호 기능 추가
# ------------------------------------------------------------
from auth import require_login

require_login()



import pandas as pd
from db import get_connection
import streamlit as st

st.set_page_config(page_title="📊 PopPang 대시보드", layout="wide")
st.title("📊 PopPang 시스템 현황")
st.caption("PopPang 운영 데이터를 한눈에 확인할 수 있는 관리자 대시보드")

# ------------------------------------------------------------
# ✅ 1. 통계 함수들
# ------------------------------------------------------------
def get_summary_stats():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM users;")
        total_users = cursor.fetchone()
        total_users = total_users["count"] if total_users else 0

        cursor.execute("SELECT COUNT(*) AS count FROM popup WHERE is_active = 1;")
        active_popups = cursor.fetchone()
        active_popups = active_popups["count"] if active_popups else 0

        cursor.execute("SELECT COUNT(*) AS count FROM popup WHERE is_active = 0;")
        inactive_popups = cursor.fetchone()
        inactive_popups = inactive_popups["count"] if inactive_popups else 0

        cursor.execute("SELECT COUNT(*) AS count FROM popup WHERE DATE(created_at) = CURDATE();")
        today_popups = cursor.fetchone()
        today_popups = today_popups["count"] if today_popups else 0

    conn.close()
    return total_users, active_popups, inactive_popups, today_popups


def get_system_status():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT name, updated_at
            FROM popup
            ORDER BY updated_at DESC
            LIMIT 1;
        """)
        last_popup = cursor.fetchone()

        cursor.execute("""
            SELECT ROUND(SUM(is_alerted = 1) / COUNT(*) * 100, 1) AS alert_ratio
            FROM users;
        """)
        alert_ratio_row = cursor.fetchone()
    conn.close()

    last_popup_name = last_popup.get("name") if last_popup else "없음"
    last_updated_at = str(last_popup.get("updated_at")) if last_popup else "-"
    alert_ratio = alert_ratio_row.get("alert_ratio") if alert_ratio_row else 0

    return last_popup_name, last_updated_at, alert_ratio


# ✅ 중복 위경도 그룹 수 계산
def get_duplicate_popup_groups():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT latitude, longitude, COUNT(*) AS count
            FROM popup
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(*) >= 2;
        """)
        rows = cursor.fetchall()
    conn.close()
    duplicate_group_count = len(rows)
    return duplicate_group_count


def get_user_trend():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DATE(created_at) AS date, COUNT(*) AS count
            FROM users
            WHERE created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 14;
        """)
        rows = cursor.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame(columns=["date", "count"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


# ------------------------------------------------------------
# ✅ 2. 주요 통계 카드
# ------------------------------------------------------------
total_users, active_popups, inactive_popups, today_popups = get_summary_stats()
last_popup_name, last_updated_at, alert_ratio = get_system_status()
duplicate_groups = get_duplicate_popup_groups()  # 🧭 추가

st.subheader("📈 주요 지표")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("전체 사용자 수", f"{total_users:,}명")
col2.metric("활성 팝업 수", f"{active_popups:,}개")
col3.metric("비활성 팝업 수", f"{inactive_popups:,}개")
col4.metric("오늘 생성된 팝업", f"{today_popups:,}개")
col5.metric("🧭 중복 좌표 그룹 수 (2개↑)", f"{duplicate_groups:,}개")

st.markdown("---")

# ------------------------------------------------------------
# ✅ 3. 시스템 상태
# ------------------------------------------------------------
# st.subheader("⚙️ 시스템 상태 요약")
# col6, col7, col8 = st.columns(3)
# col6.metric("마지막 업데이트된 팝업", last_popup_name)
# col7.metric("업데이트 시각", last_updated_at)
# col8.metric("알림 활성 사용자 비율", f"{alert_ratio}%")

# st.markdown("---")

# ------------------------------------------------------------
# ✅ 4. 사용자 가입 트렌드
# ------------------------------------------------------------
st.subheader("📊 최근 2주 사용자 가입 추이")
trend_df = get_user_trend()

if trend_df.empty:
    st.info("최근 2주간 가입 데이터가 없습니다.")
else:
    st.line_chart(
        trend_df.set_index("date")["count"],
        height=300,
        use_container_width=True
    )

# ------------------------------------------------------------
# ✅ 5. 추가 요약
# ------------------------------------------------------------
st.markdown("---")
st.caption("✅ PopPang 관리자용 통합 대시보드 — 데이터는 실시간으로 업데이트됩니다.")
