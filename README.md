# Lab

# Pyenv Setting
```bash

# 프로젝트 설치
brew install pyenv
brew install pyenv-virtualenv
pyenv install --list
pyenv install --list | grep 3.10
pyenv install 3.10.12
pyenv virtualenv 3.10.12 rng-venv

# 환경변수 설정
vi ~/.zshrc

# 븉여넣기
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# 가상환경 만들어졌는지 확인
pyenv versions

# 프로젝트 폴더와 연결
pyenv local rng-venv

# 수동 활성화
pyenv activate rng-venv
pyenv deactivate
```