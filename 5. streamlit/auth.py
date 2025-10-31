# import os
# import streamlit as st
# from dotenv import load_dotenv

# # ✅ .env 로드
# load_dotenv()

# def require_login():
#     """모든 페이지에서 공통으로 호출되는 로그인 체크 함수"""
#     if "authenticated" not in st.session_state:
#         st.session_state.authenticated = False

#     if not st.session_state.authenticated:
#         st.title("🔐 PopPang 관리자 로그인")
#         password = st.text_input("관리자 비밀번호", type="password")
#         if st.button("로그인"):
#             if password == os.getenv("ADMIN_PASSWORD"):
#                 st.session_state.authenticated = True
#                 st.success("✅ 로그인 성공!")
#                 st.rerun()
#             else:
#                 st.error("❌ 비밀번호가 올바르지 않습니다.")
#         st.stop()  # 로그인 전이면 나머지 페이지 렌더링 중단


import os
import streamlit as st
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager

# ✅ .env 로드
load_dotenv()

# ✅ 환경 변수 불러오기
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD", "default_secret_key")  # 없으면 기본값 사용

# ✅ 쿠키 관리자 생성 (password 필수!)
cookies = EncryptedCookieManager(prefix="poppang_admin_", password=COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

def require_login():
    """모든 페이지에서 공통으로 호출되는 로그인 체크 함수 (쿠키 기반 자동 로그인 유지)"""
    if cookies.get("logged_in") == "true":
        st.session_state.authenticated = True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 PopPang 관리자 로그인")
        password = st.text_input("관리자 비밀번호", type="password")

        if st.button("로그인"):
            if password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                cookies["logged_in"] = "true"
                cookies.save()
                st.success("✅ 로그인 성공! (자동 로그인 유지)")
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
        st.stop()

def logout_button():
    """로그아웃 버튼"""
    if st.button("🚪 로그아웃"):
        cookies["logged_in"] = "false"
        cookies.save()
        st.session_state.authenticated = False
        st.success("✅ 로그아웃 완료")
        st.rerun()
