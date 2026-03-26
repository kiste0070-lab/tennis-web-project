#!/usr/bin/env bash
# Render.com 배포용 크롬 자동 설치 스크립트
# Render는 진짜 무료 리눅스 서버이므로, 여기서 크롬을 직접 설치해야 봇이 작동합니다.

set -o errexit

# 1. 파이썬 라이브러리 설치
pip install -r requirements.txt

# 2. 크롬 브라우저 설치 (Headless 구동용)
STORAGE_DIR=/opt/render/project/.render
if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...크롬 설치 중 (잠시만 기다려주세요)..."
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x chrome.deb .
  rm chrome.deb
  echo "✅ 크롬 설치 완료!"
else
  echo "✅ 크롬이 이미 설치되어 있습니다."
fi
