# ✅ `make download` 명령어로 실행 가능하도록 연결
download: download-privates

# -----------------------------
# 🔐 Private 파일 다운로드
# -----------------------------
Private_Repository=team-PopPang/PopPang-Private
Private_Branch=BE
BASE_URL=https://raw.githubusercontent.com/$(Private_Repository)/$(Private_Branch)

# ✅ 파일 다운로드 함수 (Authorization 헤더에 Bearer 적용)
# $(1) = 디렉토리, $(2) = 파일명
define download_file
	mkdir -p $(1) && \
	curl -s -H "Authorization: Bearer $(GITHUB_ACCESS_TOKEN)" \
	     -o $(1)/$(2) \
	     $(BASE_URL)/$(1)/$(2)
endef

# ✅ .env 파일 없을 경우 GitHub 토큰을 받아 저장
download-privates:
	@echo "🔐 Downloading private files..."
	@if [ ! -f .env ]; then \
		read -p "Enter your GitHub access token: " token; \
		echo "GITHUB_ACCESS_TOKEN=$$token" > .env; \
	fi
	@set -a && . .env && set +a && \
	$(MAKE) _download-privates-real
	@echo "✅ Private file download complete."

# ✅ 실제 다운로드 로직 (여러 파일 추가 가능)
_download-privates-real:
	$(call download_file,PopPang,test.txt)

