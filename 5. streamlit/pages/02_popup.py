# ------------------------------------------------------------
# ✅ 0. 비밀번호 기능 추가
# ------------------------------------------------------------
from auth import require_login
require_login()

import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="🎪 팝업 관리", layout="wide")
st.title("🎪 팝업 관리")
st.caption("PopPang 앱의 팝업 스케줄 데이터 관리")

# ✅ 팝업 목록 로드
def load_popups():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, start_date, end_date, address, region,
                       insta_post_url, is_active, caption_summary,
                       latitude, longitude,
                       created_at, updated_at
                FROM popup
                ORDER BY id DESC;
            """)
            rows = cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows)
            for col in ["start_date", "end_date", "created_at", "updated_at"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# ------------------------------------------------------------
# 📋 팝업 목록 + 필터링
# ------------------------------------------------------------
st.subheader("📋 팝업 목록")

df = load_popups()

if df.empty:
    st.info("등록된 팝업이 없습니다.")
else:
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        filter_active = st.selectbox(
            "활성화 여부 필터",
            options=["전체", "활성(1)", "비활성(0)"],
            index=0
        )
    with col2:
        group_by_coords = st.checkbox("🧭 위경도 동일한 팝업끼리 묶어서 보기", value=False)

    # ✅ 활성 여부 필터
    if filter_active == "활성(1)":
        filtered_df = df[df["is_active"] == 1]
    elif filter_active == "비활성(0)":
        filtered_df = df[df["is_active"] == 0]
    else:
        filtered_df = df

# ------------------------------------------------------------
# 🧭 위경도 동일 그룹화 표시 (2개 이상인 그룹만)
# ------------------------------------------------------------
# ------------------------------------------------------------
# 🧭 위경도 동일 그룹화 표시 (2개 이상인 그룹만 + address 포함)
# ------------------------------------------------------------
if group_by_coords:
    if "latitude" in filtered_df.columns and "longitude" in filtered_df.columns:
        # 그룹화: 위도, 경도, 주소 기준
        grouped = (
            filtered_df.groupby(["latitude", "longitude", "address"])
            .agg({"id": "count"})
            .reset_index()
            .rename(columns={"id": "count"})
        )

        # ✅ 2개 이상인 그룹만 필터링
        grouped = grouped[grouped["count"] >= 2]

        if grouped.empty:
            st.info("⚠️ 동일한 위경도를 가진 팝업이 2개 이상인 그룹이 없습니다.")
        else:
            st.write("### 📍 동일 위경도 그룹 (2개 이상)")
            st.dataframe(
                grouped[["latitude", "longitude", "address", "count"]],
                use_container_width=True
            )

            st.markdown("---")
            st.write("### 🔍 그룹별 상세 보기")

            for _, row in grouped.iterrows():
                lat, lon, addr, count = row["latitude"], row["longitude"], row["address"], row["count"]
                same_coord_df = filtered_df[
                    (filtered_df["latitude"] == lat) &
                    (filtered_df["longitude"] == lon)
                ]

                with st.expander(f"📍 ({lat}, {lon}) — {count}개 팝업 | {addr}"):
                    st.dataframe(
                        same_coord_df[
                            ["id", "name", "region", "address", "start_date", "end_date", "is_active"]
                        ],
                        use_container_width=True
                    )

            st.success(f"✅ 총 {len(grouped)}개 위경도 그룹 표시 중 (2개 이상만 표시)")
    else:
        st.warning("⚠️ latitude, longitude 컬럼이 존재하지 않습니다.")
else:
    st.dataframe(filtered_df, use_container_width=True)
    st.success(f"✅ 총 {len(filtered_df)}개 팝업 표시 중 (전체 {len(df)}개)")


# ------------------------------------------------------------
# 🧩 CRUD
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🧩 팝업 관리")

tab1, tab2, tab3 = st.tabs(["➕ 추가", "🔄 수정", "🗑️ 삭제"])

# ------------------------------------------------------------
# ➕ 추가
# ------------------------------------------------------------
with tab1:
    st.write("새로운 팝업 추가")

    # ✅ 반반 정렬 (상단 기본정보)
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("팝업 이름 (필수)")
        start_date = st.date_input("시작일")
        end_date = st.date_input("종료일")
        address = st.text_input("주소")

    with col2:
        region = st.text_input("지역 (예: 서울)")
        insta_url = st.text_input("인스타그램 URL")
        is_active = st.selectbox("활성화 여부", [0, 1])

    # ✅ 요약문은 전체 아래쪽
    caption_summary = st.text_area(
        "요약문 (선택)",
        placeholder="게시글 요약문을 입력하세요",
        height=200
    )

    # ✅ 추가 버튼
    if st.button("팝업 추가"):
        if not name:
            st.warning("이름은 필수입니다.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        sql = """
                        INSERT INTO popup (name, start_date, end_date, address, region,
                                           insta_post_url, is_active, caption_summary,
                                           created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                        """
                        cursor.execute(sql, (name, start_date, end_date, address, region,
                                             insta_url, is_active, caption_summary))
                        conn.commit()
                        st.success(f"✅ '{name}' 팝업 추가 완료!")
                        st.experimental_rerun()  # ✅ 추가 후 즉시 새로고침
            except Exception as e:
                st.error(f"❌ 추가 실패: {e}")

# ------------------------------------------------------------
# 🔄 수정
# ------------------------------------------------------------
with tab2:
    st.write("기존 팝업 수정")

    edit_id = st.number_input("수정할 팝업 ID", min_value=1, step=1)

    selected_popup = None
    if edit_id and not df.empty and edit_id in df["id"].values:
        selected_popup = df[df["id"] == edit_id].iloc[0]
        st.info(f"현재 선택된 팝업: {selected_popup['name']}")
    else:
        st.caption("⚠️ 유효한 팝업 ID를 입력하면 기존 데이터를 불러옵니다.")

    new_name = st.text_input(
        "새 이름 (공백 시 유지)",
        value=selected_popup["name"] if selected_popup is not None else ""
    )

    new_active = st.selectbox(
        "활성화 여부 변경",
        [0, 1],
        index=int(selected_popup["is_active"]) if selected_popup is not None else 0
    )

    new_caption = st.text_area(
        "요약문 수정",
        value=selected_popup["caption_summary"] if selected_popup is not None else "",
        placeholder="새로운 요약문을 입력하세요",
        height=400
    )

    if st.button("팝업 수정"):
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    UPDATE popup
                    SET name = COALESCE(NULLIF(%s, ''), name),
                        is_active = %s,
                        caption_summary = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """
                    cursor.execute(sql, (new_name, new_active, new_caption, edit_id))
                    conn.commit()

                    if cursor.rowcount == 0:
                        st.warning(f"⚠️ ID {edit_id} 팝업을 찾을 수 없습니다.")
                    else:
                        st.success(f"✅ ID {edit_id} 팝업 수정 완료!")
        except Exception as e:
            st.error(f"❌ 수정 실패: {e}")

# ------------------------------------------------------------
# 🗑️ 삭제
# ------------------------------------------------------------
with tab3:
    delete_id = st.number_input("삭제할 팝업 ID", min_value=1, step=1, key="delete_popup_id")
    confirm = st.checkbox("정말로 삭제하시겠습니까? (복구 불가)")

    if st.button("삭제 실행"):
        if not confirm:
            st.warning("삭제를 진행하려면 확인란을 체크하세요.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM popup WHERE id = %s", (delete_id,))
                        conn.commit()
                        if cursor.rowcount == 0:
                            st.warning(f"⚠️ ID {delete_id} 팝업을 찾을 수 없습니다.")
                        else:
                            st.error(f"🚨 ID {delete_id} 팝업 삭제 완료.")
            except Exception as e:
                st.error(f"❌ 삭제 실패: {e}")
