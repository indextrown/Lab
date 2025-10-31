import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="👥 사용자 관리", layout="wide")
st.title("👥 사용자 관리")
st.caption("PopPang 사용자 계정 데이터 관리")

# ✅ 사용자 목록 로드 함수
def load_users():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, uid, uuid, provider, email, nickname, role,
                       is_alerted, is_deleted, created_at, updated_at
                FROM users
                ORDER BY id DESC;
            """)
            rows = cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows)
            for col in ["created_at", "updated_at"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# ✅ 사용자 목록 표시
st.subheader("📋 사용자 목록")
df = load_users()
if df.empty:
    st.info("현재 등록된 사용자가 없습니다.")
else:
    st.dataframe(df, use_container_width=True)
    st.success(f"✅ 총 {len(df)}명의 사용자를 불러왔습니다.")


# ------------------------------------------------------------
# 🧩 CRUD 기능
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🧩 사용자 관리")

tab1, tab2, tab3 = st.tabs(["➕ 추가", "🔄 수정", "🗑️ 삭제"])

# ------------------------------------------------------------
# ➕ 사용자 추가 (반반 정렬)
# ------------------------------------------------------------
with tab1:
    st.write("새로운 사용자 추가")

    col1, col2 = st.columns(2)  # 반반 나누기

    with col1:
        uid = st.text_input("UID (필수)")
        provider = st.selectbox("Provider", ["KAKAO", "GOOGLE", "APPLE"])
        nickname = st.text_input("Nickname (필수)")
        email = st.text_input("Email (선택)")

    with col2:
        role = st.selectbox("Role", ["MEMBER", "ADMIN"])
        is_alerted = st.selectbox("알림 여부", [0, 1])
        is_deleted = st.selectbox("삭제 여부", [0, 1])
        fcm_token = st.text_input("FCM Token (선택)", "")

    if st.button("사용자 추가"):
        if not uid or not nickname:
            st.warning("⚠️ UID와 닉네임은 필수입니다.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        sql = """
                        INSERT INTO users (uid, provider, email, nickname, role, 
                                           is_alerted, is_deleted, fcm_token, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                        """
                        cursor.execute(sql, (uid, provider, email or None, nickname, role, 
                                             is_alerted, is_deleted, fcm_token or None))
                        conn.commit()
                        st.success(f"✅ '{nickname}' 사용자 추가 완료!")
            except Exception as e:
                st.error(f"❌ 추가 실패: {e}")


# ------------------------------------------------------------
# 🔄 사용자 수정 (반반 정렬)
# ------------------------------------------------------------
with tab2:
    st.write("기존 사용자 정보 수정")

    col1, col2 = st.columns(2)

    with col1:
        edit_id = st.number_input("수정할 사용자 ID", min_value=1, step=1)
        new_nickname = st.text_input("새 닉네임 (공백이면 유지)")

    with col2:
        new_role = st.selectbox("새 Role", ["MEMBER", "ADMIN"])
        new_alert = st.selectbox("알림 여부 변경", [0, 1])
        new_deleted = st.selectbox("삭제 여부 변경", [0, 1])

    if st.button("정보 수정"):
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    UPDATE users
                    SET nickname = COALESCE(NULLIF(%s, ''), nickname),
                        role = %s,
                        is_alerted = %s,
                        is_deleted = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """
                    cursor.execute(sql, (new_nickname, new_role, new_alert, new_deleted, edit_id))
                    conn.commit()

                    if cursor.rowcount == 0:
                        st.warning(f"⚠️ ID {edit_id} 사용자를 찾을 수 없습니다.")
                    else:
                        st.success(f"✅ ID {edit_id} 사용자 정보 수정 완료.")
        except Exception as e:
            st.error(f"❌ 수정 실패: {e}")


# ------------------------------------------------------------
# 🗑️ 사용자 삭제 (반반 정렬)
# ------------------------------------------------------------
with tab3:
    st.write("사용자 삭제 (복구 불가 ⚠️)")
    delete_id = st.number_input("삭제할 사용자 ID", min_value=1, step=1, key="delete_user_id")
    confirm = st.checkbox("정말로 삭제하시겠습니까?")

    if st.button("삭제 실행"):
        if not confirm:
            st.warning("삭제를 진행하려면 확인란을 체크하세요.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM users WHERE id = %s", (delete_id,))
                        conn.commit()
                        if cursor.rowcount == 0:
                            st.warning(f"⚠️ ID {delete_id} 사용자를 찾을 수 없습니다.")
                        else:
                            st.error(f"🚨 ID {delete_id} 사용자 삭제 완료.")
            except Exception as e:
                st.error(f"❌ 삭제 실패: {e}")